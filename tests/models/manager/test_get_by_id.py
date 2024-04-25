import secrets
from typing import AsyncGenerator, List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order
from mongoz.exceptions import DocumentNotFound, InvalidKeyError
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


async def test_model_get_document_by_id() -> None:
    movie = await Movie.objects.create(name="Barbie", year=2023)

    a_movie = await Movie.objects.get_document_by_id(str(movie.id))
    assert movie.name == a_movie.name

    b_movie = await Movie.objects.get_document_by_id(movie.id)
    assert movie.name == b_movie.name

    with pytest.raises(InvalidKeyError):
        await Movie.objects.get_document_by_id("invalid_id")

    with pytest.raises(DocumentNotFound):
        await Movie.objects.get_document_by_id(secrets.token_hex(12))
