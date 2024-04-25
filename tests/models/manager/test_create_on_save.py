from typing import AsyncGenerator, List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, ObjectId
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.objects.delete()
    yield
    await Movie.objects.delete()


async def test_model_create_id_none() -> None:
    movie = await Movie.objects.create(name="Barbie", year=2023)
    movie.id = None

    await movie.save()

    movies = await Movie.objects.all()

    assert len(movies) == 2
