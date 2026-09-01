from typing import Any, AsyncGenerator, Dict, List, cast

import pytest
from pymongo import InsertOne
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import BulkWriteError, DuplicateKeyError

import mongoz
from mongoz import Document, Index
from tests.conftest import client

pytestmark = pytest.mark.anyio


class EscapeRecord(Document):
    label: str = mongoz.String()
    category: str = mongoz.String()
    amount: int = mongoz.Integer()

    class Meta:
        registry = client
        database = "test_db"
        collection = "escape_owner"
        indexes = [Index("label", unique=True)]


@pytest.fixture(autouse=True)
async def prepare_database() -> AsyncGenerator[None, None]:
    await client.driver["test_db"].drop_collection("escape_owner")
    await client.driver["test_escape_alternate"].drop_collection("escape_owner")
    await EscapeRecord.create_indexes()
    yield
    await client.driver["test_db"].drop_collection("escape_owner")
    await client.driver["test_escape_alternate"].drop_collection("escape_owner")


async def test_aggregation_preserves_native_pipeline_session_and_collection_semantics() -> None:
    await EscapeRecord.create_many(
        [
            EscapeRecord(label="one", category="group", amount=2),
            EscapeRecord(label="two", category="group", amount=3),
        ]
    )
    alternate = client.driver["test_escape_alternate"]["escape_owner"]
    await alternate.insert_one({"label": "alternate", "category": "group", "amount": 7})

    async with client.driver.start_session() as session:
        results = await EscapeRecord.aggregate(
            [
                {"$match": {"category": "group"}},
                {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
            ],
            session=session,
        )
        alternate_results = await EscapeRecord.aggregate(
            [{"$project": {"_id": 0, "label": 1}}],
            collection=alternate,
            session=session,
        )

    assert results == [{"_id": "group", "total": 5}]
    assert alternate_results == [{"label": "alternate"}]


async def test_collection_bulk_write_returns_native_result_and_preserves_errors() -> None:
    async with client.driver.start_session() as session:
        result = await EscapeRecord.bulk_write(
            [
                InsertOne({"label": "one", "category": "group", "amount": 1}),
                InsertOne({"label": "two", "category": "group", "amount": 2}),
            ],
            session=session,
        )
    assert result.inserted_count == 2

    with pytest.raises(BulkWriteError) as raised:
        await EscapeRecord.bulk_write(
            [
                InsertOne({"label": "three", "category": "group", "amount": 3}),
                InsertOne({"label": "one", "category": "group", "amount": 4}),
                InsertOne({"label": "four", "category": "group", "amount": 5}),
            ],
            ordered=False,
        )
    assert raised.value.details["nInserted"] == 2
    assert await EscapeRecord.objects.count() == 4

    with pytest.raises(DuplicateKeyError):
        await EscapeRecord(label="one", category="duplicate", amount=0).create()


async def test_bulk_write_collection_override_is_operation_local() -> None:
    alternate = client.driver["test_escape_alternate"]["escape_owner"]

    result = await EscapeRecord.bulk_write(
        [InsertOne({"label": "alternate", "category": "group", "amount": 1})],
        collection=alternate,
    )

    assert result.inserted_count == 1
    assert await EscapeRecord.objects.count() == 0
    assert await alternate.count_documents({}) == 1


class RecordingCursor:
    def __init__(self) -> None:
        self.documents = iter([{"value": 1}])
        self.close_count = 0

    def __aiter__(self) -> "RecordingCursor":
        return self

    async def __anext__(self) -> Dict[str, int]:
        try:
            return next(self.documents)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    async def close(self) -> None:
        self.close_count += 1


class RecordingCollection:
    def __init__(self, cursor: RecordingCursor) -> None:
        self.cursor = cursor
        self.calls: List[Dict[str, Any]] = []

    async def aggregate(self, pipeline: Any, **kwargs: Any) -> RecordingCursor:
        self.calls.append({"pipeline": pipeline, **kwargs})
        return self.cursor


async def test_aggregation_materialization_closes_the_native_cursor() -> None:
    cursor = RecordingCursor()
    recording_collection = RecordingCollection(cursor)
    collection = cast(AsyncCollection[Dict[str, Any]], recording_collection)
    session = cast(AsyncClientSession, object())

    results = await EscapeRecord.aggregate(
        [{"$match": {}}], collection=collection, session=session
    )

    assert results == [{"value": 1}]
    assert recording_collection.calls == [{"pipeline": [{"$match": {}}], "session": session}]
    assert cursor.close_count == 1
