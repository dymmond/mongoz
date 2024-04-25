from typing import List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, Index, ObjectId
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]

indexes = [
    Index("name", unique=True),
    Index("year", unique=True),
]


class BaseDocument(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)

    class Meta:
        abstract = True
        registry = client
        database = "test_db"


class Movie(BaseDocument):
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)

    class Meta:
        indexes = indexes


class Actor(BaseDocument):
    actor: str = mongoz.String(null=True)


async def test_registry() -> None:
    assert len(client.documents) > 0

    assert "Actor" in client.documents
    assert "Movie" in client.documents
