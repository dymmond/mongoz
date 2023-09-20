from typing import AsyncGenerator, List, Optional

import pydantic
import pytest
from pydantic import ValidationError
from tests.conftest import client

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order

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
    await Movie.query().delete()
    await Movie.create_indexes()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.query().delete()
    await Movie.create_indexes()


async def test_model_get_or_create() -> None:
    movie = await Movie.query({Movie.name: "Barbie"}).get_or_create({Movie.year: 2023})
    assert movie.name == "Barbie"
    assert movie.year == 2023

    movie = await Movie.query({Movie.name: "Barbie", Movie.year: 2023}).get_or_create()
    assert movie.name == "Barbie"
    assert movie.year == 2023

    movie = await Movie.query({Movie.name: "Venom"}).get_or_create({Movie.year: 2021})
    assert movie.name == "Venom"
    assert movie.year == 2021

    movie = await Movie.query({Movie.name: "Eternals", Movie.year: 2021}).get_or_create()
    assert movie.name == "Eternals"
    assert movie.year == 2021

    with pytest.raises(ValidationError):
        await movie.query({Movie.name: "Venom 2"}).get_or_create({Movie.year: "year 2021"})
