from typing import AsyncGenerator, List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, Manager, ObjectId
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)
    uuid: Optional[ObjectId] = mongoz.UUID(null=True)
    is_published: bool = mongoz.Boolean(default=False)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.objects.delete()
    yield
    await Movie.objects.delete()


async def test_model_none() -> None:
    manager = await Movie.objects.none()

    assert isinstance(manager, Manager)
    assert manager._collection == Movie.meta.collection._collection
