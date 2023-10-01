from typing import Optional

import pytest
from pymongo.errors import DuplicateKeyError
from tests.conftest import client

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order

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


async def test_raises_duplicate_error() -> None:
    await AnotherMovie.create_indexes()
    movie = await AnotherMovie.objects.create(name="Mongoz", email="mongoz@mongoz.com", year=2023)

    assert movie is not None

    with pytest.raises(DuplicateKeyError):
        await AnotherMovie.objects.create(name="Mongoz", email="mongoz@mongoz.com", year=2023)
