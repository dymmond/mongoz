from datetime import datetime
from typing import AsyncGenerator, List, Optional

import pydantic
import pytest
from bson import Code

import mongoz
from mongoz import Document, ObjectId
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)
    uuid: Optional[ObjectId] = mongoz.UUID(null=True)
    created_at: datetime = mongoz.DateTime(auto_now=True)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.drop_indexes(force=True)
    await Movie.query().delete()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.query().delete()


async def test_model_where() -> None:
    await Movie(name="Batman", year=2022).create()
    await Movie(name="Barbie", year=2023).create()

    movies = await Movie.query().where("this.name == 'Batman'")
    assert len(movies) == 1

    assert movies[0].name == "Batman"
    assert movies[0].year == 2022

    movies = await Movie.query().where("this.name == 'Barbie'")
    assert len(movies) == 1

    assert movies[0].name == "Barbie"
    assert movies[0].year == 2023

    movies = await Movie.query().where("this.name == 'barbie'")
    assert len(movies) == 0


async def test_model_where_with_object() -> None:
    await Movie(name="Batman", year=2022).create()
    await Movie(name="Barbie", year=2023).create()

    code = Code("this.name == 'Batman'")
    movies = await Movie.query().where(code)
    assert len(movies) == 1

    assert movies[0].name == "Batman"
    assert movies[0].year == 2022

    code = Code("this.name == 'Barbie'")
    movies = await Movie.query().where(code)
    assert len(movies) == 1

    assert movies[0].name == "Barbie"
    assert movies[0].year == 2023

    code = Code("this.name == 'barbie'")
    movies = await Movie.query().where(code)
    assert len(movies) == 0
