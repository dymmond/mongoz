from typing import AsyncGenerator, List, Optional

import bson
import pydantic
import pytest

import mongoz
from mongoz import Document
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Movie(Document):
    name: str = mongoz.String(index=True, unique=True)
    year: int = mongoz.Integer()
    movie_type = mongoz.String(
        choices=(
            ("H", "Horror"),
            ("C", "Comedy"),
            ("T", "Thriller"),
            ("K", "Kids"),
        )
    )
    tags: Optional[List[str]] = mongoz.Array(str, null=True)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    await Movie.create_indexes()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    await Movie.create_indexes()


async def test_model_create() -> None:
    movie = await Movie.objects.create(
        name="Barbie", year=2023, movie_type="K"
    )
    assert movie.name == "Barbie"
    assert movie.year == 2023
    assert movie.movie_type == "K"
    assert isinstance(movie.id, bson.ObjectId)
    assert movie.get_movie_type_display() == "Kids"

    try:
        movie = await Movie.objects.create(
            name="Barbie Part2", year=2024, movie_type="K2"
        )
    except ValueError as exc:
        assert (
            exc.__str__()
            == "Invalid choice for field 'movie_type'. Input provided as 'K2'"
        )
