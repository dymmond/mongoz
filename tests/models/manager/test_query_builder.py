from datetime import date, datetime
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
    released_at: datetime = mongoz.DateTime(null=True)

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


async def test_model_query_builder() -> None:
    await Movie.objects.create(
        name="Downfall", year=2004, released_at=datetime.now()
    )
    await Movie.objects.create(name="The Two Towers", year=2002)
    await Movie.objects.create(name="Casablanca", year=1942)
    await Movie.objects.create(name="Gone with the wind", year=1939)

    movie = await Movie.objects.filter(year__neq=1920).first()
    assert movie is not None

    movie = await Movie.objects.filter(year=1939).get()
    assert movie.name == "Gone with the wind"

    movie = await Movie.objects.filter(year__lt=1940).get()
    assert movie.name == "Gone with the wind"
    assert movie.year == 1939

    movie = await Movie.objects.get(year__lte=1939)
    assert movie.name == "Gone with the wind"
    assert movie.year == 1939

    movie = await Movie.objects.filter(year__gt=2000).first()
    assert movie is not None
    assert movie.name == "Downfall"
    assert movie.year == 2004

    movie = await Movie.objects.filter(year__gte=1940).first()
    assert movie is not None
    assert movie.name == "Downfall"
    assert movie.year == 2004

    movie = (
        await Movie.objects.filter(name="Casablanca").filter(year=1942).get()
    )
    assert movie.name == "Casablanca"
    assert movie.year == 1942

    movie = await Movie.objects.filter(name="Casablanca", year=1942).get()
    assert movie.name == "Casablanca"
    assert movie.year == 1942

    movie = await Movie.objects.get(name="Casablanca", year=1942)
    assert movie.name == "Casablanca"
    assert movie.year == 1942

    movie = (
        await Movie.objects.filter(year__gt=2000).filter(year__lt=2003).get()
    )
    assert movie.name == "The Two Towers"
    assert movie.year == 2002

    movie = await Movie.objects.filter(year__gt=2000, year__lt=2003).get()
    assert movie.name == "The Two Towers"
    assert movie.year == 2002

    movie = await Movie.objects.get(year__gt=2000, year__lt=2003)
    assert movie.name == "The Two Towers"
    assert movie.year == 2002

    movie = await Movie.objects.get(name__icontains="two")
    assert movie.name == "The Two Towers"
    assert movie.year == 2002

    assert (
        await Movie.objects.filter(name="Casablanca").filter(year=1942).get()
        == await Movie.objects.filter(name="Casablanca", year=1942).get()
    )
    movies = await Movie.objects.filter(name__startswith="The").all()
    assert len(movies) == 1
    assert movies[0].name == "The Two Towers"

    movies = await Movie.objects.filter(name__startswith="Cas").all()
    assert len(movies) == 1
    assert movies[0].name == "Casablanca"

    movies = await Movie.objects.filter(name__endswith="fall").all()
    assert len(movies) == 1
    assert movies[0].name == "Downfall"

    movies = await Movie.objects.filter(name__istartswith="THE").all()
    assert len(movies) == 1
    assert movies[0].name.lower() == "the Two Towers".lower()

    movies = await Movie.objects.filter(name__istartswith="CASA").all()
    assert len(movies) == 1
    assert movies[0].name.lower() == "Casablanca".lower()

    movies = await Movie.objects.filter(name__iendswith="FALL").all()
    assert len(movies) == 1
    assert movies[0].name.lower() == "downfall".lower()

    movies = await Movie.objects.filter(name__iendswith="wind").all()
    assert len(movies) == 1
    assert movies[0].name.lower() == "gone with the Wind".lower()

    movies = await Movie.objects.filter(released_at__date=date.today())
    assert len(movies) == 1
    assert movies[0].name == "Downfall"
    assert movies[0].year == 2004


async def test_query_builder_in_list():
    await Movie.objects.create(name="Downfall", year=2004)
    await Movie.objects.create(name="The Two Towers", year=2002)
    await Movie.objects.create(name="Casablanca", year=1942)
    await Movie.objects.create(name="Gone with the wind", year=1939)

    movies = await Movie.objects.filter(year__in=[2004, 2002, 1939])
    assert len(movies) == 3

    movies = await Movie.objects.filter(year__not_in=[2004, 2002])
    assert len(movies) == 2


@pytest.mark.parametrize(
    "values", [{2002, 2004}, {"year": 2002}], ids=["as-set", "as-dict"]
)
async def test_query_builder_in_list_raise_assertation_error(values):
    await Movie.objects.create(name="Downfall", year=2004)
    await Movie.objects.create(name="The Two Towers", year=2002)

    with pytest.raises(AssertionError):
        await Movie.objects.filter(year__not_in=values)
