from typing import AsyncGenerator

import pydantic
import pytest

import mongoz
from mongoz import Document, Order
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Movie(Document):
    idx: str = mongoz.Integer()

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()


async def test_model_sort_asc() -> None:
    for i in range(10):
        await Movie.objects.create(idx=i)

    movies = await Movie.objects.sort(idx__asc=True).values_list(["idx"], flatten=True)

    assert movies == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


async def test_model_sort_desc() -> None:
    for i in range(10):
        await Movie.objects.create(idx=i)

    movies = await Movie.objects.sort(idx__desc=True).values_list(["idx"], flatten=True)

    assert movies == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]


async def test_model_sort_asc_obj() -> None:
    for i in range(10):
        await Movie.objects.create(idx=i)

    movies = await Movie.objects.sort("idx", Order.ASCENDING).values_list(["idx"], flatten=True)

    assert movies == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


async def test_model_sort_obj() -> None:
    for i in range(10):
        await Movie.objects.create(idx=i)

    movies = await Movie.objects.sort("idx", Order.DESCENDING).values_list(["idx"], flatten=True)

    assert movies == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
