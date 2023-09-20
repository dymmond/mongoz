from typing import AsyncGenerator, List, Optional

import pydantic
import pytest
from tests.conftest import client

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order, Q

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


async def test_model_sort() -> None:
    await Movie(name="Oppenheimer", year=2023).create()
    await Movie(name="Batman", year=2022).create()

    movies = await Movie.query().sort("name", Order.ASCENDING).all()

    assert movies[0].name == "Batman"
    assert movies[1].name == "Oppenheimer"

    movies = await Movie.query().sort(Movie.name, Order.ASCENDING).all()

    assert movies[0].name == "Batman"
    assert movies[1].name == "Oppenheimer"

    movies = await Movie.query().sort([(Movie.name, Order.DESCENDING)]).all()

    assert movies[0].name == "Oppenheimer"
    assert movies[1].name == "Batman"

    movies = (
        await Movie.query()
        .sort([(Movie.name, Order.DESCENDING), (Movie.year, Order.DESCENDING)])
        .all()
    )

    assert movies[0].name == "Oppenheimer"
    assert movies[1].name == "Batman"

    movies = (
        await Movie.query()
        .sort(Movie.name, Order.DESCENDING)
        .sort(Movie.year, Order.ASCENDING)
        .all()
    )

    assert movies[0].name == "Oppenheimer"
    assert movies[1].name == "Batman"

    movies = await Movie.query().sort(Q.asc(Movie.name)).all()
    assert movies[0].name == "Batman"
    assert movies[1].name == "Oppenheimer"

    movies = await Movie.query().sort(Q.desc(Movie.name)).sort(Q.asc(Movie.year)).all()
    assert movies[0].name == "Oppenheimer"
    assert movies[1].name == "Batman"
