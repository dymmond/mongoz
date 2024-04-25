from typing import AsyncGenerator

import pydantic
import pytest
from pymongo.errors import DuplicateKeyError

import mongoz
from mongoz import Document
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Movie(Document):
    name: str = mongoz.String(unique=True)
    is_published: bool = mongoz.Boolean(default=False)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    await Movie.create_indexes()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    await Movie.create_indexes()


async def test_unique():
    movie = await Movie.objects.create(name="Barbie")

    assert movie.is_published is False

    with pytest.raises(DuplicateKeyError):
        await Movie.objects.create(name="Barbie")
