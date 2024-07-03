from decimal import Decimal
from typing import AsyncGenerator

import pydantic
import pytest

import mongoz
from mongoz import Document
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Archive(Document):
    name: str = mongoz.String()
    price: Decimal = mongoz.Decimal(max_digits=5, decimal_places=2, null=True)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Archive.objects.delete()
    yield
    await Archive.objects.delete()


async def test_decimal_128() -> None:
    await Archive.objects.create(name="Batman", price=22.246)

    arch = await Archive.objects.last()
    assert float(str(arch.price)) == 22.246


async def test_decimal_128_two() -> None:
    await Archive.objects.create(name="Batman", price="22.246")

    arch = await Archive.objects.last()
    assert float(str(arch.price)) == 22.246
