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


async def test_model_skip() -> None:
    await Movie(name="Oppenheimer", year=2003).create()
    await Movie(name="Batman", year=2022).create()

    movies = (
        await Movie.query().sort(Movie.name, Order.ASCENDING).skip(1).all()
    )
    assert len(movies) == 1
    assert movies[0].name == "Oppenheimer"

    movie = await Movie.query().sort(Movie.name, Order.ASCENDING).skip(1).get()
    assert movie.name == "Oppenheimer"
