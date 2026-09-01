import asyncio
from typing import Any, Dict, List

import pytest

from mongoz.core.db.querysets.core.manager import Manager
from mongoz.core.db.querysets.core.queryset import QuerySet
from mongoz.core.db.querysets.expressions import Expression

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

    def find(self, filter_query: Dict[str, Any], **kwargs: Any) -> RecordingCursor:
        self.filters.append({"filter": filter_query, **kwargs})
        return self.cursor


class AggregateCollection:
    def __init__(self, cursor: RecordingCursor) -> None:
        self.cursor = cursor
        self.pipelines: List[List[Dict[str, Any]]] = []

    async def aggregate(self, pipeline: List[Dict[str, Any]], **kwargs: Any) -> RecordingCursor:
        self.pipelines.append([*pipeline, {"__options__": kwargs}])
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
    queryset._session = None
    return queryset


async def test_find_returns_cursor_without_await_and_early_close_releases_it() -> None:
    cursor = RecordingCursor([{"value": 1}, {"value": 2}])
    collection = FindCollection(cursor)
    iterator = make_manager(collection).__aiter__()

    document = await anext(iterator)
    await iterator.aclose()

    assert document.values == {"value": 1}
    assert collection.filters == [{"filter": {}}]
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
    assert collection.pipelines == [[{"__options__": {}}]]
    assert cursor.close_count == 1


async def test_queryset_find_materializes_once_then_closes() -> None:
    cursor = RecordingCursor([{"value": 1}, {"value": 2}])
    collection = FindCollection(cursor)

    documents = await make_queryset(collection).all()

    assert [document.values for document in documents] == [
        {"value": 1},
        {"value": 2},
    ]
    assert collection.filters == [{"filter": {}}]
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


async def test_manager_derivations_do_not_share_mutable_query_state() -> None:
    parent = make_manager(AggregateCollection(RecordingCursor([])))

    first = parent.raw(Expression("value", "$eq", 1)).sort("value")
    second = parent.raw(Expression("value", "$eq", 2)).sort("other")

    assert parent._filter == []
    assert parent._sort == []
    assert [(item.key, item.value) for item in first._filter] == [("value", 1)]
    assert [item.key for item in first._sort] == ["value"]
    assert [(item.key, item.value) for item in second._filter] == [("value", 2)]
    assert [item.key for item in second._sort] == ["other"]


async def test_queryset_derivations_do_not_share_mutable_query_state() -> None:
    parent = make_queryset(FindCollection(RecordingCursor([])))

    first = parent.query(Expression("value", "$eq", 1)).sort("value").limit(1)
    second = parent.query(Expression("value", "$eq", 2)).sort("other").skip(2)

    assert parent._filter == []
    assert parent._sort == []
    assert parent._limit_count == 0
    assert parent._skip_count == 0
    assert [(item.key, item.value) for item in first._filter] == [("value", 1)]
    assert [item.key for item in first._sort] == ["value"]
    assert first._limit_count == 1
    assert [(item.key, item.value) for item in second._filter] == [("value", 2)]
    assert [item.key for item in second._sort] == ["other"]
    assert second._skip_count == 2


async def test_manager_compiles_skip_once_and_propagates_session() -> None:
    session = object()
    collection = AggregateCollection(RecordingCursor([]))

    await make_manager(collection).using_session(session).skip(3)._all()

    assert collection.pipelines == [[{"$skip": 3}, {"__options__": {"session": session}}]]


async def test_queryset_propagates_session_to_find() -> None:
    session = object()
    collection = FindCollection(RecordingCursor([]))

    await make_queryset(collection).using_session(session).all()

    assert collection.filters == [{"filter": {}, "session": session}]
