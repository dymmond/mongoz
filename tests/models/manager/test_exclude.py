from typing import AsyncGenerator, List, Optional

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


async def test_model_exclude() -> None:
    batman = await Movie.objects.create(name="Batman", year=2022)
    await Movie.objects.create(name="Barbie", year=2023)
    await Movie.objects.create(name="Oppenheimer", year=2023)

    movies = await Movie.objects.exclude(pk=batman.id)

    assert len(movies) == 2


async def xtest_models_exclude() -> None:
    await Movie.objects.create(name="Batman", year=2022)
    await Movie.objects.create(name="Barbie", year=2023)
    await Movie.objects.create(name="Oppenheimer", year=2023)

    movies = await Movie.objects.exclude(year__gt=2019)

    assert len(movies) == 0
