from typing import Optional

import pytest
from tests.conftest import client

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order
from mongoz.exceptions import InvalidKeyError

pytestmark = pytest.mark.anyio

indexes = [
    Index(keys=[("year", Order.DESCENDING), ("genre", IndexType.HASHED)]),
]


class Movie(Document):
    name: str = mongoz.String(index=True, unique=True)
    year: int = mongoz.Integer()
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)

    class Meta:
        registry = client
        indexes = indexes
        database = "test_db"


async def test_create_indexes() -> None:
    index_names = [index.name for index in Movie.meta.indexes]
    assert index_names == ["name", "year_genre"]

    await Movie.drop_indexes()

    index = await Movie.create_index("name")
    assert index == "name"

    with pytest.raises(InvalidKeyError):
        await Movie.create_index("random_index")
