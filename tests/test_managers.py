from datetime import datetime
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
    uuid: Optional[ObjectId] = mongoz.UUID(null=True)
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)


class Course(mongoz.EmbeddedDocument):
    code: str = mongoz.String()
    name: str = mongoz.String()
    start_date: datetime = mongoz.DateTime()
    end_date: datetime = mongoz.DateTime()


class Student(BaseDocument):
    name: str = mongoz.String()
    roll_no: int = mongoz.Integer()
    courses: List[Course] = mongoz.Array(Course, default=[])


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


async def test_filter():
    cn = Course(
        code="CN",
        name="Computer Network",
        start_date="2025-09-22",
        end_date="2026-04-30",
    )
    os = Course(
        code="OS",
        name="Operating System",
        start_date="2025-04-22",
        end_date="2026-04-30",
    )
    ml = Course(
        code="ML",
        name="Machine Learning",
        start_date="2025-04-22",
        end_date="2025-12-31",
    )
    cs = Course(
        code="CS",
        name="Cyber Security",
        start_date="2025-01-01",
        end_date="2025-04-30",
    )
    pe = Course(
        code="PE",
        name="Prompt Engg.",
        start_date="2025-09-22",
        end_date="2026-04-30",
    )
    await Student.objects.create(
        name="Harshali", roll_no=2022, courses=[cn, os, cs, pe]
    )
    await Student.objects.create(
        name="Samit", roll_no=2023, courses=[cn, os, pe]
    )
    await Student.objects.create(
        name="Tanaji", roll_no=2024, courses=[cn, os, ml, cs, pe]
    )
    await Student.objects.filter().values_list(["roll_no"], flat=True)
    roll_nos = await Student.objects.filter(
        **{"courses.code": "CS"}
    ).values_list(["role_no"], flat=True)

    assert roll_nos.sort() == [2022, 2023]
