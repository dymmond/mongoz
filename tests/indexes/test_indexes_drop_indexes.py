from typing import Optional

import pytest

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order
from tests.conftest import client

pytestmark = pytest.mark.anyio

indexes = [
    Index(keys=[("year", Order.DESCENDING), ("genre", IndexType.HASHED)]),
]


class AnotherMovie(Document):
    name: str = mongoz.String()
    email: str = mongoz.Email(index=True, unique=True)
    year: int = mongoz.Integer()
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)

    class Meta:
        registry = client
        indexes = indexes
        database = "test_db"
        autogenerate_index = True


async def test_drops_indexes() -> None:
    await AnotherMovie.create_indexes()
    await AnotherMovie.objects.create(name="Mongoz", email="mongoz@mongoz.com", year=2023)

    total_indexes = await AnotherMovie.list_indexes()

    assert len(total_indexes) == 3

    # Change the indexes to be dropped
    AnotherMovie.meta.fields["email"].index = False
    AnotherMovie.meta.fields["email"].unique = False

    await AnotherMovie.check_indexes()

    total_indexes = await AnotherMovie.list_indexes()

    assert len(total_indexes) == 2

    # Complex
    await AnotherMovie.create_indexes()

    total_indexes = await AnotherMovie.list_indexes()

    assert len(total_indexes) == 3

    # Change the indexes to be dropped
    AnotherMovie.meta.fields["email"].index = False
    AnotherMovie.meta.fields["email"].unique = False

    AnotherMovie.meta.indexes.pop(1)

    await AnotherMovie.check_indexes()

    total_indexes = await AnotherMovie.list_indexes()

    assert len(total_indexes) == 1


async def test_drops_indexes_different_db() -> None:
    await AnotherMovie.objects.using("another_test_db").delete()
    collection = AnotherMovie.objects.using("another_test_db")._collection
    await AnotherMovie.create_indexes(collection=collection)
    await AnotherMovie.objects.using("another_test_db").create(
        name="Mongoz", email="mongoz@mongoz.com", year=2023)

    total_indexes = await AnotherMovie.list_indexes(collection=collection)

    assert len(total_indexes) == 3
