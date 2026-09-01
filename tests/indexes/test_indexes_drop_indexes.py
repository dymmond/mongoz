from typing import AsyncGenerator, Optional

import pytest

import mongoz
from mongoz import Document, Index, IndexAction, IndexType, ObjectId, Order
from tests.conftest import client

pytestmark = pytest.mark.anyio

indexes = [
    Index(keys=[("year", Order.DESCENDING), ("genre", IndexType.HASHED)]),
]


class AnotherMovie(Document):
    name: str = mongoz.String()
    email: str = mongoz.Email(index=True, unique=True)
    year: int = mongoz.Integer()
    uuid: Optional[ObjectId] = mongoz.UUID(null=True)

    class Meta:
        registry = client
        indexes = indexes
        database = "test_db"
        autogenerate_index = True


class Movie(Document):
    name: str = mongoz.String()
    email: str = mongoz.Email(index=True, unique=True)
    year: int = mongoz.Integer()
    uuid: Optional[ObjectId] = mongoz.UUID(null=True)

    class Meta:
        registry = client
        database = "test_db"
        autogenerate_index = True


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    collection = Movie.objects.using("another_test_db")._collection
    await Movie.drop_indexes(force=True, collection=collection)
    await Movie.objects.using("another_test_db").delete()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.objects.using("another_test_db").delete()


async def test_drops_indexes() -> None:
    await AnotherMovie.create_indexes()
    await AnotherMovie.objects.create(name="Mongoz", email="mongoz@mongoz.com", year=2023)
    await AnotherMovie.get_collection().create_index("name", name="manual_name")

    plan = await AnotherMovie.check_indexes()

    total_indexes = await AnotherMovie.list_indexes()
    assert {index["name"] for index in total_indexes} == {
        "_id_",
        "email",
        "manual_name",
        "year_genre",
    }
    assert [entry.name for entry in plan.actions(IndexAction.RETAIN)] == [
        "_id_",
        "manual_name",
    ]


async def test_drops_indexes_different_db() -> None:
    collection = Movie.objects.using("another_test_db")._collection
    await Movie.create_indexes(collection=collection)
    await Movie.objects.using("another_test_db").create(
        name="Mongoz", email="mongoz@mongoz.com", year=2023
    )
    total_indexes = await Movie.list_indexes(collection=collection)

    assert len(total_indexes) == 2
