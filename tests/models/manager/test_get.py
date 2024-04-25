from typing import AsyncGenerator, List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order
from mongoz.exceptions import DocumentNotFound, MultipleDocumentsReturned
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


async def test_model_get() -> None:
    await Movie.objects.create(name="Barbie", year=2023)

    movie = await Movie.objects.get()
    assert movie.name == "Barbie"

    await Movie.objects.create(name="Batman", year=2013)

    movie = await Movie.objects.filter(name="Barbie").get()
    assert movie.name == "Barbie"

    movie = await Movie.objects.filter(_id=movie.id).get()
    assert movie.name == "Barbie"

    movie = await Movie.objects.filter(id=movie.id).get()
    assert movie.name == "Barbie"

    movie = await Movie.objects.filter(pk=movie.id).get()
    assert movie.name == "Barbie"

    with pytest.raises(DocumentNotFound):
        await Movie.objects.filter(name="Interstellar").get()

    with pytest.raises(MultipleDocumentsReturned):
        await Movie.objects.get()


async def test_model_get_by_kwargs() -> None:
    await Movie.objects.create(name="Barbie", year=2023)

    movie = await Movie.objects.get()
    assert movie.name == "Barbie"

    await Movie.objects.create(name="Batman", year=2013)

    movie = await Movie.objects.get(name="Barbie")
    assert movie.name == "Barbie"

    movie = await Movie.objects.get(_id=movie.id)
    assert movie.name == "Barbie"

    movie = await Movie.objects.get(id=movie.id)
    assert movie.name == "Barbie"

    movie = await Movie.objects.get(pk=movie.id)
    assert movie.name == "Barbie"

    with pytest.raises(DocumentNotFound):
        await Movie.objects.get(name="Interstellar")

    with pytest.raises(MultipleDocumentsReturned):
        await Movie.objects.get()
