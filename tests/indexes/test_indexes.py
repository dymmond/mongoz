from typing import Optional

import pytest

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order
from mongoz.exceptions import InvalidKeyError
from tests.conftest import client

pytestmark = pytest.mark.anyio

indexes = [
    Index("name", unique=True),
    Index(keys=[("year", Order.DESCENDING), ("genre", IndexType.HASHED)]),
]


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)

    class Meta:
        registry = client
        indexes = indexes
        database = "test_db"


async def test_create_indexes() -> None:
    index_names = await Movie.create_indexes()
    assert index_names == ["name", "year_genre"]

    await Movie.drop_indexes()

    index = await Movie.create_index("name")
    assert index == "name"

    with pytest.raises(InvalidKeyError):
        await Movie.create_index("random_index")
