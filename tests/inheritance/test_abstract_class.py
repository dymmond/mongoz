from typing import AsyncGenerator, List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, Index, ObjectId
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]

indexes = [
    Index("name", unique=True),
    Index("year", unique=True),
]


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

    class Meta:
        indexes = indexes


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.drop_indexes(force=True)
    await Movie.query().delete()
    await Movie.create_indexes()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.query().delete()
    await Movie.create_indexes()


async def test_model_all() -> None:
    movies = await BaseDocument.query().all()
    assert len(movies) == 0

    await BaseDocument(name="Barbie", year=2003).create()

    movies = await BaseDocument.query().all()
    assert len(movies) == 1
