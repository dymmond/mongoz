from typing import Optional

import pytest

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order
from mongoz.exceptions import IndexError
from tests.conftest import client

pytestmark = pytest.mark.anyio


async def test_create_indexes() -> None:
    with pytest.raises(IndexError):

        class Movie(Document):
            name: str = mongoz.String(index=True, unique=True)
            year: int = mongoz.Integer()
            uuid: Optional[ObjectId] = mongoz.UUID(null=True)

            class Meta:
                registry = client
                indexes = [
                    Index("name", unique=True),
                    Index(
                        keys=[
                            ("year", Order.DESCENDING),
                            ("genre", IndexType.HASHED),
                        ]
                    ),
                ]
                database = "test_db"
