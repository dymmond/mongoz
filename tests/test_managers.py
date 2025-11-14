from __future__ import annotations

from datetime import datetime
from typing import AsyncGenerator, ClassVar, List, Optional

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


class Producer(BaseDocument):

    name: str = mongoz.String()
    age: int = mongoz.Integer()
    movie_types: Optional[List[str]] = mongoz.Array(str, null=True)


class Movie(BaseDocument):
    uuid: Optional[ObjectId] = mongoz.UUID(null=True)
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)
    producer_id: ObjectId = mongoz.ForeignKey(Producer, null=True)


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
async def prepare_database() -> AsyncGenerator:
    await Student.query().delete()
    await Movie.query().delete()
    yield
    await Movie.query().delete()
    await Student.query().delete()


async def test_custom_abstraction():
    barbie = await Movie.bigger.create(name="Barbie", year=2023)
    die_hard = await Movie.smaller.create(name="Die Hard", year=2022)

    total = await Movie.objects.count()

    assert total == 2

    total_bigger = await Movie.bigger.all()
    assert total_bigger[0].id == barbie.id

    total_smaller = await Movie.smaller.all()
    assert total_smaller[0].id == die_hard.id


async def test_embedded_filter():
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

    # Embedded search
    roll_nos = await Student.objects.filter(
        **{"courses.code": "CS"}
    ).values_list(["roll_no"], flat=True)

    roll_nos.sort()
    assert roll_nos == [2022, 2024]


async def test_reference_filter():
    producer1 = await Producer.objects.create(
        name="Jhon", age=56, movie_types=["Horror", "Anime"]
    )
    producer2 = await Producer.objects.create(
        name="Alok", age=46, movie_types=["Thriller", "Anime"]
    )
    producer3 = await Producer.objects.create(
        name="Prasad", age=36, movie_types=["Horror", "Action"]
    )

    await Movie.objects.create(
        name="Barbie", year=2022, producer_id=producer2.id
    )
    await Movie.objects.create(
        name="Haunted House", year=2024, producer_id=producer1.id
    )
    await Movie.objects.create(
        name="The Ghost", year=2023, producer_id=producer3.id
    )

    # Fetch the movie object.
    movie = await Movie.objects.get(producer_id__age__gte=50)
    assert movie.producer_id == producer1.id
    assert movie.name == "Haunted House"
    assert movie.year == 2024
    producer_obj = movie.lookup_on_producer_id[0]
    assert producer_obj.id == producer1.id
    assert producer_obj.name == producer1.name
    assert producer_obj.age == producer1.age
    assert producer_obj.movie_types == producer1.movie_types

    # Fetch the Movie using the values.
    movies = await Movie.objects.filter(producer_id__age__gte=50).values(
        ["name", "producer_id__movie_types"]
    )
    assert len(movies) == 1
    movie_obj = movies[0]
    assert movie_obj["name"] == movie.name
    assert len(movie_obj["lookup_on_producer_id"]) == 1
    producer_obj = movie_obj["lookup_on_producer_id"][0]
    assert producer_obj["movie_types"] == producer1.movie_types
