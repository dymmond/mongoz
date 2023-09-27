import random
import sys
from typing import AsyncGenerator, List, Optional

import bson
import pydantic
import pytest
from tests.conftest import client

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order

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
    await Movie.objects.delete()
    await Movie.create_indexes()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    await Movie.create_indexes()


@pytest.mark.skipif(sys.version_info < (3, 10), reason="zip() implementation refactored in 3.10+")
async def test_model_create_many() -> None:
    movies = []
    movie_names = ("The Dark Knight", "The Dark Knight Rises", "The Godfather")
    for movie_name in movie_names:
        movies.append(Movie(name=movie_name, year=random.randint(1970, 2020)))

    movies_db = await Movie.objects.create_many(movies)
    for movie, movie_db in zip(movies, movies_db):
        assert movie.name == movie_db.name
        assert movie.year == movie_db.year
        assert isinstance(movie.id, bson.ObjectId)

    class Book(Document):
        name: str = mongoz.String()
        year: int = mongoz.Integer()

        class Meta:
            indexes = indexes
            database = "test_db"

    with pytest.raises(TypeError):
        book = Book(name="The Book", year=1972)
        movie = Movie(name="Inception", year=2010)
        await Movie.create_many([book, movie])  # type: ignore
