from decimal import Decimal
from typing import AsyncGenerator

import pydantic
import pytest

import mongoz
from mongoz import Document
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Movie(Document):
    name: str = mongoz.String()
    price: Decimal = mongoz.Decimal(max_digits=5, decimal_places=2, null=True)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.objects.delete()
    yield
    await Movie.objects.delete()


async def test_decimal_128() -> None:
    await Movie.objects.create(name="Batman", price=22.246)

    movie = await Movie.objects.last()
    assert float(str(movie.price)) == 22.246


async def test_decimal_128_two() -> None:
    await Movie.objects.create(name="Batman", price="22.246")

    movie = await Movie.objects.last()
    assert float(str(movie.price)) == 22.246
