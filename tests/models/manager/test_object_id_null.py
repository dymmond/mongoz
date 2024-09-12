from typing import AsyncGenerator

import pydantic
import pytest
from pydantic_core import ValidationError

import mongoz
from mongoz import Document, ObjectId
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    producer_id: mongoz.ObjectId = mongoz.NullableObjectId()

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.objects.delete()
    yield
    await Movie.objects.delete()


async def test_nullable_objectid() -> None:
    await Movie.objects.using("test_my_db").delete()
    await Movie.objects.using("test_my_db").create(name="latest_movie", year=2024)

    movie = await Movie.objects.using("test_my_db").get()
    assert movie.name == "latest_movie"
    assert movie.year == 2024
    assert movie.producer_id is None


async def test_nullable_objectid_raises_error_on_type() -> None:
    with pytest.raises(ValidationError):
        await Movie.objects.create(name="latest_movie", year=2024, producer_id=123)

    await Movie.objects.create(name="latest_movie", year=2024)

    movie = await Movie.objects.last()

    with pytest.raises(ValueError):
        movie.producer_id = 1234


async def test_nullable_objectid_on_set() -> None:
    await Movie.objects.create(name="latest_movie", year=2024)

    movie = await Movie.objects.last()
    producer_id = ObjectId()

    movie.producer_id = producer_id
    await movie.save()

    movie = await Movie.objects.last()
    assert movie.name == "latest_movie"
    assert movie.year == 2024
    assert str(movie.producer_id) == str(producer_id)


async def test_nullable_objectid_result() -> None:
    producer_id = ObjectId()

    await Movie.objects.create(name="latest_movie", year=2024, producer_id=producer_id)

    movie = await Movie.objects.last()

    assert movie.name == "latest_movie"
    assert movie.year == 2024
    assert str(movie.producer_id) == str(producer_id)
