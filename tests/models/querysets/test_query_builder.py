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


async def test_model_query_builder() -> None:
    await Movie(name="Downfall", year=2004).create()
    await Movie(name="The Two Towers", year=2002).create()
    await Movie(name="Casablanca", year=1942).create()
    await Movie(name="Gone with the wind", year=1939).create()

    movie = await Movie.query(Movie.year != 1920).first()
    assert movie is not None

    movie = await Movie.query(Movie.year == 1939).get()
    assert movie.name == "Gone with the wind"

    movie = await Movie.query(Movie.year < 1940).get()
    assert movie.name == "Gone with the wind"
    assert movie.year == 1939

    movie = await Movie.query(Movie.year <= 1939).get()
    assert movie.name == "Gone with the wind"
    assert movie.year == 1939

    movie = await Movie.query(Movie.year > 2000).first()
    assert movie is not None
    assert movie.name == "Downfall"
    assert movie.year == 2004

    movie = await Movie.query(Movie.year >= 1940).first()
    assert movie is not None
    assert movie.name == "Downfall"
    assert movie.year == 2004

    movie = await Movie.query(Movie.name == "Casablanca").query(Movie.year == 1942).get()
    assert movie.name == "Casablanca"
    assert movie.year == 1942

    movie = await Movie.query(Movie.year > 2000).query(Movie.year < 2003).get()
    assert movie.name == "The Two Towers"
    assert movie.year == 2002

    assert (
        await Movie.query(Movie.name == "Casablanca").query(Movie.year == 1942).get()
        == await Movie.query(Movie.name == "Casablanca", Movie.year == 1942).get()
    )
