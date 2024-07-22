from decimal import Decimal
from typing import AsyncGenerator

import bson
import pydantic
import pytest
from bson import Decimal128

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


async def test_decimal_128_create_many() -> None:
    archives = []
    archive_names = ("The Dark Knight", "The Dark Knight Rises", "The Godfather")
    for movie_name in archive_names:
        archives.append(Archive(name=movie_name, price=Decimal("22.246")))

    archives_db = await Archive.objects.create_many(archives)
    for archive, archive_db in zip(archives, archives_db):
        assert archive.name == archive_db.name
        assert archive.price == archive_db.price
        assert isinstance(archive.id, bson.ObjectId)


async def test_decimal_on_update() -> None:
    await Archive.objects.create(name="Batman", price="22.246")

    arch = await Archive.objects.last()

    arch.price = Decimal("28")
    await arch.save()

    arch = await Archive.objects.last()

    assert arch.price == Decimal128("28")

    await arch.update(price=Decimal("30"))

    arch = await Archive.objects.last()

    assert arch.price == Decimal128("30")

    await Archive.objects.filter().update(price=Decimal("40"))

    arch = await Archive.objects.last()

    assert arch.price == Decimal128("40")
