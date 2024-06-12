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
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)

    class Meta:
        registry = client
        database = "test_db"
        indexes = indexes
        autogenerate_index = True


async def test_model_using() -> None:
    await Movie.create_indexes_for_multiple_databases(["test_my_db", "test_second_db"])

    await Movie.objects.create(name="Mongoz", email="mongoz@mongoz.com", year=2023)
    await Movie.objects.using("test_my_db").create(
        name="Mongoz", email="mongoz@mongoz.com", year=2023
    )

    await Movie.objects.using("test_second_db").create(
        name="Mongoz", email="mongoz@mongoz.com", year=2023
    )
    with pytest.raises(DuplicateKeyError):
        await Movie.objects.create(name="Mongoz", email="mongoz@mongoz.com", year=2023)

    with pytest.raises(DuplicateKeyError):
        await Movie.objects.using("test_my_db").create(
            name="Mongoz", email="mongoz@mongoz.com", year=2023
        )
    with pytest.raises(DuplicateKeyError):
        await Movie.objects.using("test_second_db").create(
            name="Mongoz", email="mongoz@mongoz.com", year=2023
        )
