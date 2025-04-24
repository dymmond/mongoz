from typing import AsyncGenerator

import pydantic
import pytest

import mongoz
from mongoz import Document
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Producer(Document):
    name: str = mongoz.String()
    mobile_no: str = mongoz.String()
    email: str = mongoz.String()

    class Meta:
        registry = client
        database = "test_db"


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    producer_id: mongoz.ObjectId = mongoz.ForeignKey(model=Producer)

    class Meta:
        registry = client
        database = "test_db"


class AnotherMovie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    producer_id: mongoz.ObjectId = mongoz.ForeignKey(model=Producer, null=True)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Producer.objects.delete()
    await Movie.objects.delete()
    await AnotherMovie.objects.delete()
    yield
    await Producer.objects.delete()
    await Movie.objects.delete()
    await AnotherMovie.objects.delete()


async def test_foreign_field() -> None:
    producer = await Producer.objects.create(
        name="Harshali Zode", mobile_no="9990099000", email="example.gmail.com"
    )
    movie = await Movie.objects.create(
        name="Barbie", year=2025, producer_id=producer.id
    )
    assert movie.model_fields["producer_id"].model == Producer
    assert (
        movie.model_fields["producer_id"].model.Meta.collection.name
        == "producers"
    )
    ForeignModel = movie.model_fields["producer_id"].model

    result = await ForeignModel.objects.get(id=movie.producer_id)
    assert result.name == producer.name
    assert result.mobile_no == producer.mobile_no
    assert result.email == producer.email


async def test_nullable_foreign_field() -> None:
    movie = await AnotherMovie.objects.create(name="Barbie", year=2025)
    assert movie.model_fields["producer_id"].model == Producer
    assert (
        movie.model_fields["producer_id"].model.Meta.collection.name
        == "producers"
    )
