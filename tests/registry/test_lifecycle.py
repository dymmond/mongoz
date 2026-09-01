import asyncio
from typing import AsyncGenerator
from unittest.mock import patch

import pytest
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import InvalidOperation, OperationFailure, ServerSelectionTimeoutError

import mongoz
from mongoz import Document, Registry
from tests.settings import TEST_DATABASE_URL

pytestmark = pytest.mark.anyio


@pytest.fixture
async def registry() -> AsyncGenerator[Registry, None]:
    registry = Registry(TEST_DATABASE_URL)
    yield registry
    await registry.close()


async def test_registry_owns_and_reuses_one_native_client(registry: Registry) -> None:
    driver = registry.driver
    first_database = registry.get_database("test_db")
    second_database = registry.get_database("test_db")
    collection = first_database.get_collection("registry_lifecycle")

    assert isinstance(driver, AsyncMongoClient)
    assert isinstance(first_database._db, AsyncDatabase)
    assert isinstance(collection._collection, AsyncCollection)
    assert registry.driver is driver
    assert first_database._db.client is driver
    assert second_database._db.client is driver
    assert collection._collection.database.client is driver

    assert (await first_database._db.command("ping"))["ok"] == 1
    assert await registry.address is not None


async def test_registry_preserves_native_client_options_and_redacts_default_repr() -> None:
    username = "manifest-user"
    password = "manifest-password"
    url = (
        f"mongodb://{username}:{password}@127.0.0.1:1/"
        "?serverSelectionTimeoutMS=123&connectTimeoutMS=456&socketTimeoutMS=789"
        "&waitQueueTimeoutMS=321&timeoutMS=654&retryReads=false&retryWrites=false"
        "&readPreference=secondaryPreferred&w=majority&readConcernLevel=majority"
    )
    registry = Registry(url)
    options = registry.driver.options

    assert options.server_selection_timeout == pytest.approx(0.123)
    assert options.pool_options.connect_timeout == pytest.approx(0.456)
    assert options.pool_options.socket_timeout == pytest.approx(0.789)
    assert options.pool_options.wait_queue_timeout == pytest.approx(0.321)
    assert options.timeout == pytest.approx(0.654)
    assert options.retry_reads is False
    assert options.retry_writes is False
    assert options.read_preference.name == "SecondaryPreferred"
    assert options.write_concern.document == {"w": "majority"}
    assert options.read_concern.level == "majority"

    for rendered in (repr(registry), str(registry), repr(registry.driver), str(registry.driver)):
        assert username not in rendered
        assert password not in rendered
        assert url not in rendered
    await registry.close()


async def test_close_is_final_and_idempotent(registry: Registry) -> None:
    driver = registry.driver
    database = registry.get_database("test_db")
    await database._db.command("ping")

    await registry.close()
    await registry.close()

    assert registry.is_closed is True
    with pytest.raises(RuntimeError, match="Registry is closed"):
        registry.get_database("test_db")
    with pytest.raises(RuntimeError, match="Registry is closed"):
        _ = registry.driver
    with pytest.raises(InvalidOperation, match="after close"):
        await database._db.command("ping")
    with pytest.raises(InvalidOperation, match="after close"):
        await driver.get_database("test_db").command("ping")


async def test_close_before_first_operation_is_supported() -> None:
    registry = Registry(TEST_DATABASE_URL)

    await registry.close()
    await registry.close()

    assert registry.is_closed is True
    with pytest.raises(RuntimeError, match="Registry is closed"):
        await registry.__aenter__()


async def test_context_manager_closes_on_normal_exit() -> None:
    registry = Registry(TEST_DATABASE_URL)

    async with registry as entered:
        assert entered is registry
        assert (await registry.get_database("admin")._db.command("ping"))["ok"] == 1

    assert registry.is_closed is True


async def test_context_manager_closes_without_swallowing_exception() -> None:
    registry = Registry(TEST_DATABASE_URL)

    with pytest.raises(LookupError, match="application failure"):
        async with registry:
            await registry.get_database("admin")._db.command("ping")
            raise LookupError("application failure")

    assert registry.is_closed is True


async def test_context_manager_preserves_body_error_when_cleanup_fails() -> None:
    registry = Registry(TEST_DATABASE_URL)
    cleanup_error = RuntimeError("cleanup failure")

    with patch.object(registry, "close", side_effect=cleanup_error):
        with pytest.raises(LookupError, match="application failure") as raised:
            async with registry:
                raise LookupError("application failure")

    assert raised.value.__cause__ is cleanup_error
    await registry.close()


async def test_driver_rejects_cross_event_loop_use(registry: Registry) -> None:
    await registry.get_database("admin")._db.command("ping")

    def use_registry_in_another_loop() -> None:
        asyncio.run(registry.get_databases())

    with pytest.raises(RuntimeError, match="different event loop"):
        await asyncio.to_thread(use_registry_in_another_loop)

    assert (await registry.get_database("admin")._db.command("ping"))["ok"] == 1


async def test_cross_event_loop_close_does_not_mark_registry_closed(
    registry: Registry,
) -> None:
    await registry.get_database("admin")._db.command("ping")

    def close_registry_in_another_loop() -> None:
        asyncio.run(registry.close())

    with pytest.raises(RuntimeError, match="different event loop"):
        await asyncio.to_thread(close_registry_in_another_loop)

    assert registry.is_closed is False
    assert (await registry.get_database("admin")._db.command("ping"))["ok"] == 1


async def test_server_selection_failure_is_preserved_and_cleanup_still_works() -> None:
    registry = Registry("mongodb://127.0.0.1:1/?serverSelectionTimeoutMS=50&connectTimeoutMS=50")

    with pytest.raises(ServerSelectionTimeoutError):
        await registry.get_database("test_db")._db.command("ping")

    await registry.close()
    assert registry.is_closed is True


async def test_authentication_failure_preserves_native_error_without_credentials() -> None:
    username = "manifest-user"
    password = "manifest-password"
    url = (
        f"mongodb://{username}:{password}@127.0.0.1:27017/"
        "?authSource=admin&serverSelectionTimeoutMS=1000"
    )
    registry = Registry(url)

    with pytest.raises(OperationFailure) as raised:
        await registry.driver.admin.command("ping")

    message = str(raised.value)
    assert username not in message
    assert password not in message
    assert url not in message
    await registry.close()


async def test_cancellation_is_preserved_and_cleanup_still_works() -> None:
    registry = Registry(
        "mongodb://127.0.0.1:1/?serverSelectionTimeoutMS=10000&connectTimeoutMS=10000"
    )
    operation = asyncio.create_task(registry.get_databases())
    await asyncio.sleep(0.05)

    operation.cancel()
    with pytest.raises(asyncio.CancelledError):
        await operation

    await registry.close()
    assert registry.is_closed is True


async def test_document_checks_perform_explicit_async_index_initialization() -> None:
    registry = Registry(TEST_DATABASE_URL)
    lifecycle_registry = registry

    class LifecycleIndexedDocument(Document):
        slug: str = mongoz.String(index=True, unique=True)

        class Meta:
            registry = lifecycle_registry
            database = "test_registry_lifecycle"
            autogenerate_index = True

    try:
        await LifecycleIndexedDocument.objects.create(slug="bootstrap")
        indexes_before = await LifecycleIndexedDocument.list_indexes()
        assert [index["name"] for index in indexes_before] == ["_id_"]

        await registry.document_checks()

        indexes_after = await LifecycleIndexedDocument.list_indexes()
        assert {index["name"] for index in indexes_after} == {"_id_", "slug"}
    finally:
        await registry.drop_database("test_registry_lifecycle")
        await registry.close()


async def test_repeated_queryset_evaluation_uses_fresh_native_cursors() -> None:
    registry = Registry(TEST_DATABASE_URL)
    lifecycle_registry = registry

    class CursorDocument(Document):
        sequence: int = mongoz.Integer()

        class Meta:
            registry = lifecycle_registry
            database = "test_registry_lifecycle"

    try:
        await CursorDocument.objects.create(sequence=1)
        await CursorDocument.objects.create(sequence=2)
        queryset = CursorDocument.query().sort("sequence")

        first = await queryset.all()
        second = await queryset.all()

        assert [document.sequence for document in first] == [1, 2]
        assert [document.sequence for document in second] == [1, 2]
    finally:
        await registry.drop_database("test_registry_lifecycle")
        await registry.close()
