from typing import ClassVar, List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, Index, ObjectId
from mongoz.core.db.documents.managers import QuerySetManager
from mongoz.core.db.querysets.base import Manager
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]

indexes = [
    Index("name", unique=True),
    Index("year", unique=True),
]


class BiggerManager(QuerySetManager):

    def get_queryset(self) -> Manager:
        return super().get_queryset().filter(year__gte=2023)


class SmallerManager(QuerySetManager):

    def get_queryset(self) -> Manager:
        return super().get_queryset().filter(year__lte=2022)


class BaseDocument(Document):
    bigger: ClassVar[BiggerManager] = BiggerManager()
    smaller: ClassVar[SmallerManager] = SmallerManager()

    class Meta:
        abstract = True
        registry = client
        database = "test_db"


class Movie(BaseDocument):
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
    barbie = await Movie.bigger.create(name="Barbie", year=2023)
    die_hard = await Movie.smaller.create(name="Die Hard", year=2022)

    total = await Movie.objects.count()

    assert total == 2

    total_bigger = await Movie.bigger.all()
    assert total_bigger[0].id == barbie.id

    total_smaller = await Movie.smaller.all()
    assert total_smaller[0].id == die_hard.id
