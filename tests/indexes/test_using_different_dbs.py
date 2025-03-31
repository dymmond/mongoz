from typing import Optional

import pydantic
import pytest
from pymongo.errors import DuplicateKeyError

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


indexes = [
    Index(keys=[("year", Order.DESCENDING), ("genre", IndexType.HASHED)]),
]


class Movie(Document):
    name: str = mongoz.String()
    email: str = mongoz.Email(index=True, unique=True)
    year: int = mongoz.Integer()
    uuid: Optional[ObjectId] = mongoz.UUID(null=True)

    class Meta:
        registry = client
        database = "test_db"
        indexes = indexes


class IdMap(Document):
    objectid1: ObjectId = mongoz.ObjectId()
    objectid2: ObjectId = mongoz.ObjectId()

    class Meta:
        registry = client
        database = "test_db"
        indexes = [
            mongoz.Index(
                keys=[
                    ("objectid1", mongoz.Order.DESCENDING),
                    ("objectid2", mongoz.Order.DESCENDING),
                ],
                unique=True,
            )
        ]


async def test_model_using() -> None:
    await Movie.create_indexes_for_multiple_databases(
        ["test_my_db", "test_second_db"]
    )

    await Movie.objects.create(
        name="Mongoz", email="mongoz@mongoz.com", year=2023
    )
    await Movie.objects.using("test_my_db").create(
        name="Mongoz", email="mongoz@mongoz.com", year=2023
    )

    await Movie.objects.using("test_second_db").create(
        name="Mongoz", email="mongoz@mongoz.com", year=2023
    )
    with pytest.raises(DuplicateKeyError):
        await Movie.objects.create(
            name="Mongoz", email="mongoz@mongoz.com", year=2023
        )

    with pytest.raises(DuplicateKeyError):
        await Movie.objects.using("test_my_db").create(
            name="Mongoz", email="mongoz@mongoz.com", year=2023
        )
    with pytest.raises(DuplicateKeyError):
        await Movie.objects.using("test_second_db").create(
            name="Mongoz", email="mongoz@mongoz.com", year=2023
        )


async def test_model_using_with_ids() -> None:
    await IdMap.create_indexes_for_multiple_databases(
        ["test_my_db", "test_second_db"]
    )
    objectid1 = ObjectId()
    objectid2 = ObjectId()
    await IdMap.objects.create(objectid1=objectid1, objectid2=objectid2)
    await IdMap.objects.using("test_my_db").create(
        objectid1=objectid1, objectid2=objectid2
    )

    await IdMap.objects.using("test_second_db").create(
        objectid1=objectid1, objectid2=objectid2
    )
    with pytest.raises(DuplicateKeyError):
        await IdMap.objects.create(objectid1=objectid1, objectid2=objectid2)
    with pytest.raises(DuplicateKeyError):
        await IdMap.objects.using("test_my_db").create(
            objectid1=objectid1, objectid2=objectid2
        )
    with pytest.raises(DuplicateKeyError):
        await IdMap.objects.using("test_second_db").create(
            objectid1=objectid1, objectid2=objectid2
        )
