import re
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


async def test_custom_query_operators() -> None:
    await Movie.objects.create(
        name="The Two Towers", year=2002, tags=["Fantasy", "Adventure"]
    )
    await Movie.objects.create(name="Two Tales", year=2023, tags=["scify"])
    await Movie.objects.create(name="Downfall", year=2004, tags=["Drama"])
    await Movie.objects.create(
        name="Boyhood", year=2010, tags=["Coming Of Age", "Drama"]
    )

    movies = await Movie.objects.filter(year__in=[2000, 2001, 2002])

    assert len(movies) == 1
    assert movies[0].name == "The Two Towers"

    movies = (
        await Movie.objects.filter(year__gt=2000)
        .filter(year__lte=2010)
        .filter(year__not_in=[2001, 2002])
    )

    assert len(movies) == 2
    assert movies[0].name == "Boyhood"
    assert movies[1].name == "Downfall"

    # movies = await Movie.query(Q.or_(Movie.name == "The Two Towers", Movie.year > 2005)).all()
    # assert movies[0].name == "The Two Towers"
    # assert movies[1].name == "Boyhood"

    # movie = await Movie.query(Q.and_(Movie.name == "The Two Towers", Movie.year > 2000)).get()
    # assert movie.name == "The Two Towers"

    # movie = (
    #     await Movie.query(Q.and_(Movie.name == "The Two Towers", Movie.year > 2000))
    #     .query(Movie.name == "The Two Towers")
    #     .get()
    # )
    # assert movie.name == "The Two Towers"

    # count = (
    #     await Movie.query(Q.and_(Movie.name == "The Two Towers", Movie.year > 2000))
    #     .query(Movie.name == "Boyhood")
    #     .count()
    # )
    # assert count == 0

    movies = await Movie.objects.filter(tags__contains="Drama").all()
    assert movies[0].name == "Downfall"
    assert movies[1].name == "Boyhood"

    movies = await Movie.objects.filter(name__contains="Two").all()
    assert movies[0].name == "The Two Towers"

    movies = await Movie.objects.filter(name__pattern=r"\w+ Two \w+").all()
    assert len(movies) == 1
    assert movies[0].name == "The Two Towers"

    movies = await Movie.objects.filter(
        name__pattern=re.compile(r"\w+ Two \w+")
    ).all()
    assert len(movies) == 1
    assert movies[0].name == "The Two Towers"

    movies = await Movie.objects.filter(name__pattern=r"\w+ The \w+").all()
    assert len(movies) == 0
