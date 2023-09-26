from typing import AsyncGenerator, List, Optional

import pydantic
import pytest
from tests.conftest import client

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order
from mongoz.exceptions import DocumentNotFound, MultipleDumentsReturned

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
    await Movie.query().delete()
    await Movie.create_indexes()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.query().delete()
    await Movie.create_indexes()


async def test_model_get() -> None:
    await Movie(name="Barbie", year=2023).create()

    movie = await Movie.query().get()
    assert movie.name == "Barbie"

    await Movie(name="Batman", year=2013).create()

    movie = await Movie.query({Movie.name: "Barbie"}).get()
    assert movie.name == "Barbie"

    movie = await Movie.query({"_id": movie.id}).get()
    assert movie.name == "Barbie"

    movie = await Movie.query({Movie.id: movie.id}).get()
    assert movie.name == "Barbie"

    with pytest.raises(DocumentNotFound):
        await Movie.query({Movie.name: "Interstellar"}).get()

    with pytest.raises(MultipleDumentsReturned):
        await Movie.query().get()
