from typing import ClassVar, List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, Index, ObjectId
from mongoz.core.db.querysets.base import Manager
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]

indexes = [
    Index("name", unique=True),
    Index("year", unique=True),
]


class CustomManager(Manager): ...


class BaseDocument(Document):
    objects: ClassVar[CustomManager] = CustomManager()

    class Meta:
        abstract = True
        registry = client
        database = "test_db"


class Movie(BaseDocument):
    all_manager: ClassVar[CustomManager] = CustomManager()
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)


@pytest.fixture(scope="function", autouse=True)
async def prepare_database():
    await Movie.query().delete()
    yield
    await Movie.query().delete()


async def test_custom_abstraction():
    await Movie.all_manager.create(name="Barbie", year=2023)

    total = await Movie.objects.count()

    assert total == 1
