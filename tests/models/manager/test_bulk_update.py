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
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)

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


async def test_model_bulk_update_many() -> None:
    await Movie.objects.create(name="Boyhood", year=2004)
    await Movie.objects.create(name="Boyhood-2", year=2011)

    movies = await Movie.objects.filter(year=2004).update_many(year=2010)
    assert movies[0].year == 2010

    movies = await Movie.objects.all()
    assert movies[0].year == 2010

    movies = await Movie.objects.filter(name="Boyhood-2").update_many(year=2010)
    assert len(movies) == 1
    assert movies[0].year == 2010

    movies = await Movie.objects.filter(year=2010)
    assert len(movies) == 2

    movies = await Movie.objects.filter(name="Boyhood-2").update_many(year=2014, name="Boyhood 2")
    assert movies[0].year == 2014
    assert movies[0].name == "Boyhood 2"

    with pytest.raises(pydantic.ValidationError):
        movies = await Movie.objects.filter(name="Boyhood 2").update_many(year="test")

    movies = await Movie.objects.filter(name="Boyhood 2").update_many(test=2021)
    assert movies[0].year == 2014
    assert movies[0].name == "Boyhood 2"


async def test_model_bulk_update() -> None:
    await Movie.objects.create(name="Boyhood", year=2004)
    await Movie.objects.create(name="Boyhood-2", year=2011)

    movies = await Movie.objects.filter(year=2004).update(year=2010)
    assert movies[0].year == 2010

    movies = await Movie.objects.all()
    assert movies[0].year == 2010

    movies = await Movie.objects.filter(name="Boyhood-2").update(year=2010)
    assert len(movies) == 1
    assert movies[0].year == 2010

    movies = await Movie.objects.filter(year=2010)
    assert len(movies) == 2

    movies = await Movie.objects.filter(name="Boyhood-2").update(year=2014, name="Boyhood 2")
    assert movies[0].year == 2014
    assert movies[0].name == "Boyhood 2"

    with pytest.raises(pydantic.ValidationError):
        movies = await Movie.objects.filter(name="Boyhood 2").update(year="test")

    movies = await Movie.objects.filter(name="Boyhood 2").update(test=2021)
    assert movies[0].year == 2014
    assert movies[0].name == "Boyhood 2"


async def test_model_bulk_update_function() -> None:
    await Movie.objects.create(name="Boyhood", year=2004)
    await Movie.objects.create(name="Boyhood-2", year=2011)

    movies = await Movie.objects.filter(year=2004).bulk_update(year=2010)
    assert movies[0].year == 2010

    movies = await Movie.objects.all()
    assert movies[0].year == 2010

    movies = await Movie.objects.filter(name="Boyhood-2").bulk_update(year=2010)
    assert len(movies) == 1
    assert movies[0].year == 2010

    movies = await Movie.objects.filter(year=2010)
    assert len(movies) == 2

    movies = await Movie.objects.filter(name="Boyhood-2").bulk_update(year=2014, name="Boyhood 2")
    assert movies[0].year == 2014
    assert movies[0].name == "Boyhood 2"

    with pytest.raises(pydantic.ValidationError):
        movies = await Movie.objects.filter(name="Boyhood 2").bulk_update(year="test")

    movies = await Movie.objects.filter(name="Boyhood 2").bulk_update(test=2021)
    assert movies[0].year == 2014
    assert movies[0].name == "Boyhood 2"
