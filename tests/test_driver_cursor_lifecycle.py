import asyncio
from typing import Any, Dict, List

import pytest

from mongoz.core.db.querysets.core.manager import Manager
from mongoz.core.db.querysets.core.queryset import QuerySet

pytestmark = pytest.mark.anyio


class DummyDocument:
    def __init__(self, **values: Any) -> None:
        self.values = values

    @classmethod
    def from_row(cls, row: Dict[str, Any], **kwargs: Any) -> "DummyDocument":
        return cls(**row)


class RecordingCursor:
    def __init__(
        self,
        documents: List[Dict[str, Any]],
        block: bool = False,
        close_error: BaseException | None = None,
    ) -> None:
        self.documents = iter(documents)
        self.block = block
        self.close_error = close_error
        self.started = asyncio.Event()
        self.close_count = 0

    def __aiter__(self) -> "RecordingCursor":
        return self

    async def __anext__(self) -> Dict[str, Any]:
        self.started.set()
        if self.block:
            await asyncio.Event().wait()
        try:
            return next(self.documents)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    async def close(self) -> None:
        self.close_count += 1
        if self.close_error is not None:
            raise self.close_error


class FindCollection:
    def __init__(self, cursor: RecordingCursor) -> None:
        self.cursor = cursor
        self.filters: List[Dict[str, Any]] = []

    def find(self, filter_query: Dict[str, Any]) -> RecordingCursor:
        self.filters.append(filter_query)
        return self.cursor


class AggregateCollection:
    def __init__(self, cursor: RecordingCursor) -> None:
        self.cursor = cursor
        self.pipelines: List[List[Dict[str, Any]]] = []

    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> RecordingCursor:
        self.pipelines.append(pipeline)
        return self.cursor


def make_manager(collection: Any) -> Manager:
    manager = Manager()
    manager.model_class = DummyDocument
    manager._collection = collection
    return manager


def make_queryset(collection: Any) -> QuerySet:
    queryset = QuerySet.__new__(QuerySet)
    queryset.model_class = DummyDocument
    queryset._collection = collection
    queryset._filter = []
    queryset._sort = []
    queryset._skip_count = 0
    queryset._limit_count = 0
    queryset._only_fields = []
    queryset._defer_fields = []
    return queryset


async def test_find_returns_cursor_without_await_and_early_close_releases_it() -> None:
    cursor = RecordingCursor([{"value": 1}, {"value": 2}])
    collection = FindCollection(cursor)
    iterator = make_manager(collection).__aiter__()

    document = await anext(iterator)
    await iterator.aclose()

    assert document.values == {"value": 1}
    assert collection.filters == [{}]
    assert cursor.close_count == 1


async def test_cursor_cancellation_is_not_swallowed_and_releases_cursor() -> None:
    cursor = RecordingCursor([], block=True)
    manager = make_manager(FindCollection(cursor))

    async def consume() -> None:
        async for _ in manager:
            pass

    operation = asyncio.create_task(consume())
    await cursor.started.wait()
    operation.cancel()

    with pytest.raises(asyncio.CancelledError):
        await operation
    assert cursor.close_count == 1


async def test_cleanup_failure_does_not_replace_cursor_cancellation() -> None:
    cleanup_error = RuntimeError("cursor cleanup failed")
    cursor = RecordingCursor([], block=True, close_error=cleanup_error)
    manager = make_manager(AggregateCollection(cursor))
    operation = asyncio.create_task(manager._all())
    await cursor.started.wait()
    operation.cancel()

    with pytest.raises(asyncio.CancelledError):
        await operation
    assert cursor.close_count == 1


async def test_cleanup_failure_is_chained_to_materialization_failure() -> None:
    cleanup_error = RuntimeError("cursor cleanup failed")
    cursor = RecordingCursor([{"value": 1}], close_error=cleanup_error)
    manager = make_manager(AggregateCollection(cursor))

    class FailingDocument:
        @classmethod
        def from_row(cls, row: Dict[str, Any], **kwargs: Any) -> None:
            raise LookupError("materialization failed")

    manager.model_class = FailingDocument

    with pytest.raises(LookupError, match="materialization failed") as raised:
        await manager._all()
    assert raised.value.__cause__ is cleanup_error
    assert cursor.close_count == 1


async def test_aggregate_is_awaited_and_materialized_once_then_closed() -> None:
    cursor = RecordingCursor([{"value": 1}, {"value": 2}])
    collection = AggregateCollection(cursor)
    manager = make_manager(collection)

    documents = await manager._all()

    assert [document.values for document in documents] == [
        {"value": 1},
        {"value": 2},
    ]
    assert collection.pipelines == [[]]
    assert cursor.close_count == 1


async def test_queryset_find_materializes_once_then_closes() -> None:
    cursor = RecordingCursor([{"value": 1}, {"value": 2}])
    collection = FindCollection(cursor)

    documents = await make_queryset(collection).all()

    assert [document.values for document in documents] == [
        {"value": 1},
        {"value": 2},
    ]
    assert collection.filters == [{}]
    assert cursor.close_count == 1


async def test_aggregate_cancellation_is_not_swallowed_and_releases_cursor() -> None:
    cursor = RecordingCursor([], block=True)
    manager = make_manager(AggregateCollection(cursor))
    operation = asyncio.create_task(manager._all())
    await cursor.started.wait()
    operation.cancel()

    with pytest.raises(asyncio.CancelledError):
        await operation
    assert cursor.close_count == 1
