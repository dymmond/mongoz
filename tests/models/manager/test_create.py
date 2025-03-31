from typing import AsyncGenerator, List, Optional

import bson
import pydantic
import pytest
from pydantic import ValidationError
from pymongo import errors

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
    uuid: Optional[ObjectId] = mongoz.UUID(null=True)

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


async def test_model_create() -> None:
    movie = await Movie.objects.create(name="Barbie", year=2023)
    assert movie.name == "Barbie"
    assert movie.year == 2023
    assert isinstance(movie.id, bson.ObjectId)

    with pytest.raises(ValidationError) as exc:
        await Movie.objects.create(name="Justice League", year=2017, uuid="1")

    error = exc.value.errors()[0]

    assert error["type"] == "uuid_parsing"
    assert error["loc"] == ("uuid",)
    assert (
        error["msg"]
        == "Input should be a valid UUID, invalid length: expected length 32 for simple format, found 1"
    )
    assert error["input"] == "1"

    with pytest.raises(errors.DuplicateKeyError):
        await Movie.objects.create(name="Barbie", year=2023)
