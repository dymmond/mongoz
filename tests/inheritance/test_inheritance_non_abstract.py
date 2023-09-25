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
        registry = client
        database = "test_db"


class Movie(BaseDocument):
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)


class Actor(BaseDocument):
    movies: Optional[List[Any]] = mongoz.ArrayList(null=True)


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await BaseDocument.query().delete()
    await Movie.query().delete()
    await Actor.query().delete()
    yield
    await BaseDocument.query().delete()
    await Movie.query().delete()
    await Actor.query().delete()


async def test_model_non_abstract() -> None:
    movies = await BaseDocument.query().all()
    assert len(movies) == 0

    await BaseDocument(name="Barbie", year=2003).create()

    movies = await BaseDocument.query().all()
    assert len(movies) == 1

    cursor = BaseDocument.query()
    async for movie in cursor:
        assert movie.name == "Barbie"


async def test_model_all() -> None:
    movies = await Movie.query().all()
    assert len(movies) == 0

    await Movie(name="Barbie", year=2003).create()

    movies = await Movie.query().all()
    assert len(movies) == 1

    cursor = Movie.query()
    async for movie in cursor:
        assert movie.name == "Barbie"


async def test_model_nested_inherited() -> None:
    actors = await Actor.query().all()
    assert len(actors) == 0

    await Actor(name="Paul Rudd", year=1972, movies=["Only Murders in the Building"]).create()

    actors = await Actor.query().all()
    assert len(actors) == 1

    actors = Actor.query()
    async for movie in actors:
        assert movie.name == "Paul Rudd"
        assert movie.movies[0] == "Only Murders in the Building"
