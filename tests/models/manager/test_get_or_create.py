from typing import AsyncGenerator, List, Optional

import pydantic
import pytest
from pydantic import ValidationError

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]

indexes = [
    Index("name", unique=True),
    Index(keys=[("year", Order.DESCENDING), ("genre", IndexType.HASHED)]),
]


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)

    class Meta:
        registry = client
        database = "test_db"
        indexes = indexes


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    await Movie.create_indexes()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    await Movie.create_indexes()


async def test_model_get_or_create() -> None:
    movie = await Movie.objects.filter(name="Barbie").get_or_create({"year": 2023})
    assert movie.name == "Barbie"
    assert movie.year == 2023

    movie = await Movie.objects.filter(name="Barbie", year=2023).get_or_create()
    assert movie.name == "Barbie"
    assert movie.year == 2023

    movie = await Movie.objects.filter(name="Venom").get_or_create({"year": 2021})
    assert movie.name == "Venom"
    assert movie.year == 2021

    movie = await Movie.objects.filter(name="Eternals", year=2021).get_or_create()
    assert movie.name == "Eternals"
    assert movie.year == 2021

    with pytest.raises(ValidationError):
        await movie.objects.filter(name="Venom 2").get_or_create({"year": "year 2021"})
