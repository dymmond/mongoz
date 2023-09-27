from datetime import datetime
from typing import AsyncGenerator, List, Optional

import pydantic
import pytest
from tests.conftest import client

import mongoz
from mongoz import Document, ObjectId

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)
    created_at: datetime = mongoz.DateTime(auto_now=True)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()


async def test_model_distinct() -> None:
    await Movie(name="Batman", year=2022).create()
    await Movie(name="Barbie", year=2023).create()

    movies = await Movie.objects.distinct_values("name")
    assert len(movies) == 2

    assert "Barbie" in movies
    assert "Batman" in movies
