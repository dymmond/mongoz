from typing import Any, AsyncGenerator, List, Optional

import pydantic
import pytest
from pydantic import ValidationError

import mongoz
from mongoz import Document, ObjectId
from tests.conftest import client

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
    uuid: Optional[ObjectId] = mongoz.UUID(null=True)


class Actor(BaseDocument):
    movies: Optional[List[Any]] = mongoz.ArrayList(null=True)


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.query().delete()
    await Actor.query().delete()
    yield
    await Movie.query().delete()
    await Actor.query().delete()


async def test_array() -> None:
    movies = await Movie.query().all()
    assert len(movies) == 0

    await Movie(name="Barbie", year=2023, tags=["barbie"]).create()

    movies = await Movie.query().all()
    assert len(movies) == 1

    cursor = Movie.query()
    async for movie in cursor:
        assert movie.name == "Barbie"
        assert movie.tags == ["barbie"]

    await Movie(name="Batman", year=2022, tags=["detective", "dc"]).create()

    movies = await Movie.query().all()

    movie = movies[1]
    assert movie.name == "Batman"
    assert movie.tags == ["detective", "dc"]


async def test_array_error() -> None:
    movies = await Movie.query().all()
    assert len(movies) == 0

    with pytest.raises(ValidationError):
        await Movie(name="Barbie", year=2003, tags=["barbie", 1]).create()


async def test_model_nested_inherited() -> None:
    actors = await Actor.query().all()
    assert len(actors) == 0

    await Actor(
        name="Paul Rudd", year=1972, movies=["Only Murders in the Building"]
    ).create()

    actors = await Actor.query().all()
    assert len(actors) == 1

    actors = Actor.query()
    async for movie in actors:
        assert movie.name == "Paul Rudd"
        assert movie.movies[0] == "Only Murders in the Building"

    await Actor(
        name="Margot Robbie", year=1990, movies=["Barbie", 3, 2.25]
    ).create()

    actors = await Actor.query().all()
    actor = actors[1]

    assert actor.name == "Margot Robbie"
    assert actor.movies == ["Barbie", 3, 2.25]
