from typing import AsyncGenerator, List, Optional

import pydantic
import pytest

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
    is_published: bool = mongoz.Boolean(default=False)

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


async def test_model_all() -> None:
    movies = await Movie.query().all()
    assert len(movies) == 0

    await Movie(name="Forrest Gump", year=2003, is_published=True).create()

    movies = await Movie.query().all()
    assert len(movies) == 1

    cursor = Movie.query()
    async for movie in cursor:
        assert movie.name == "Forrest Gump"
        assert movie.is_published is True


async def test_model_default() -> None:
    movies = await Movie.query().all()
    assert len(movies) == 0

    await Movie(name="Ghostbusters - Afterlife 2", year=2024).create()

    movies = await Movie.query().all()
    assert len(movies) == 1

    cursor = Movie.query()
    async for movie in cursor:
        assert movie.name == "Ghostbusters - Afterlife 2"
        assert movie.is_published is False
