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
    is_published: bool = mongoz.Boolean(default=False)

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


async def test_exists_true() -> None:
    movies = await Movie.objects.all()
    assert len(movies) == 0

    await Movie.objects.create(
        name="Forrest Gump", year=2003, is_published=True
    )

    assert await Movie.objects.exists(name="Forrest Gump") is True
    assert await Movie.objects.exists(name="Forrest Gump", year=2003) is True
    assert await Movie.objects.exists(name="Forrest Gump", year=2004) is False

    assert await Movie.objects.filter(name="Forrest Gump").exists() is True
    assert (
        await Movie.objects.filter(name="Forrest Gump", year=2003).exists()
        is True
    )
    assert (
        await Movie.objects.filter(name="Forrest Gump", year=2004).exists()
        is False
    )
