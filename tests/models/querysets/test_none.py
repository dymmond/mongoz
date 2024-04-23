from typing import AsyncGenerator, List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, ObjectId, QuerySet
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)
    is_published: bool = mongoz.Boolean(default=False)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.query().delete()
    yield
    await Movie.query().delete()


async def test_model_none() -> None:
    queryset = await Movie.query().none()

    assert isinstance(queryset, QuerySet)
    assert queryset._collection == Movie.meta.collection._collection
