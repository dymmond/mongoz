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
    await Movie.objects.delete()
    await Movie.create_indexes()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    await Movie.create_indexes()


async def test_raw_queries() -> None:
    await Movie.objects.create(name="Gone with the wind", year=1939)
    await Movie.objects.create(name="Casablanca", year=1942)
    await Movie.objects.create(name="The Two Towers", year=2002)
    await Movie.objects.create(name="Downfall", year=2004)
    await Movie.objects.create(name="Boyhood", year=2010)

    movie = await Movie.objects.raw({"name": "Casablanca"}).get()

    assert movie.name == "Casablanca"
    assert movie.year == 1942

    movie = await Movie.objects.raw({"year": {"$lt": 1940}}).get()

    assert movie.name == "Gone with the wind"
    assert movie.year == 1939

    movie = await Movie.objects.raw({"year": {"$lt": 2003, "$gt": 2000}}).get()

    assert movie.name == "The Two Towers"
    assert movie.year == 2002

    # movie = await Movie.query({"year": {"$gt": 2000}}).query({"year": {"$lt": 2003}}).get()
    movie = (
        await Movie.objects.raw({"year": {"$gt": 2000}})
        .raw({"year": {"$lt": 2003}})
        .get()
    )

    assert movie.name == "The Two Towers"
    assert movie.year == 2002

    movie = (
        await Movie.objects.raw({"year": 1942})
        .raw({"name": {"$regex": "Casa"}})
        .get()
    )

    assert movie.name == "Casablanca"
    assert movie.year == 1942

    movie = (
        await Movie.objects.raw({"name": "Casablanca"})
        .raw({"year": {"$lt": 1950}})
        .get()
    )

    assert movie.name == "Casablanca"
    assert movie.year == 1942

    movie = await Movie.objects.raw(
        {"$and": [{"name": "Casablanca", "year": 1942}]}
    ).get()

    assert movie.name == "Casablanca"
    assert movie.year == 1942

    movies = await Movie.objects.raw(
        {"$or": [{"name": "The Two Towers"}, {"year": {"$gt": 2005}}]}
    ).all()

    assert movies[0].name == "The Two Towers"
    assert movies[1].name == "Boyhood"
