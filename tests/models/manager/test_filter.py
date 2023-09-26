from typing import Any, AsyncGenerator, List, Optional

import pydantic
import pytest
from tests.conftest import client

import mongoz
from mongoz import Document, ObjectId

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class BaseDocument(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)

    class Meta:
        abstract = True
        registry = client
        database = "test_db"


class Movie(BaseDocument):
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)


class Actor(BaseDocument):
    movies: Optional[List[Any]] = mongoz.ArrayList(null=True)


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.objects.delete()
    await Actor.objects.delete()
    yield
    await Movie.objects.delete()
    await Actor.objects.delete()


async def test_filter() -> None:
    barbie = await Movie.objects.create(name="Barbie", year=2023, tags=["barbie"])

    movies = await Movie.objects.all()
    assert len(movies) == 1

    movies = await Movie.objects.filter(name="Barbie")

    assert len(movies) == 1
    assert movies[0].name == barbie.name
    assert movies[0].tags == barbie.tags

    cursor = Movie.query()
    async for movie in cursor:
        assert movie.name == "Barbie"
        assert movie.tags == ["barbie"]

    batman = await Movie.objects.create(name="Batman", year=2022, tags=["detective", "dc"])
    movies = await Movie.objects.all()

    assert len(movies) == 2

    movie = movies[1]
    assert movie.name == batman.name
    assert movie.tags == batman.tags
