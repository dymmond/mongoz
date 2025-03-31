from typing import List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, Index, ObjectId
from mongoz.exceptions import AbstractDocumentError
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
    uuid: Optional[ObjectId] = mongoz.UUID(null=True)

    class Meta:
        indexes = indexes


async def test_abstract_error() -> None:
    with pytest.raises(AbstractDocumentError):
        await BaseDocument.query().all()

    with pytest.raises(AbstractDocumentError):
        await BaseDocument(name="Barbie", year=2003).create()
