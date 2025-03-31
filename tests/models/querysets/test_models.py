from typing import AsyncGenerator, List, Optional

import pytest

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order
from tests.conftest import client

pytestmark = pytest.mark.anyio

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
    await Movie.query().delete()
    await Movie.create_indexes()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.query().delete()
    await Movie.create_indexes()


def test_model_class() -> None:
    class Product(Document):
        sku: str = mongoz.String()

        class Meta:
            registry = client
            database = "test_db"

    with pytest.raises(ValueError):
        Product(sku=12345)

    movie = Movie(name="Batman", year=2009)
    movie_dump = movie.model_dump()

    assert movie_dump == dict(movie)
    assert movie_dump["name"] == "Batman"
    assert movie_dump["year"] == 2009
    assert movie_dump["id"] is None
    assert movie_dump["tags"] is None

    assert Movie.meta.database.name == "test_db"
    assert Movie.meta.collection.name == "movies"
