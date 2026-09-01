from collections.abc import AsyncGenerator

import pytest

import mongoz
from mongoz import Collection
from mongoz.core.db import documents, fields, querysets
from mongoz.core.signals import __all__ as signal_exports
from mongoz.exceptions import __all__ as exception_exports
from mongoz.protocols import QuerySetProtocol
from tests.conftest import client

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
async def test_database() -> AsyncGenerator[None, None]:
    """Keep public API inventory tests independent from MongoDB availability."""
    yield


async def test_declared_public_exports_exist_and_are_unique() -> None:
    modules_and_exports = (
        (mongoz, mongoz.__all__),
        (documents, documents.__all__),
        (fields, fields.__all__),
        (querysets, querysets.__all__),
        (mongoz.core.signals, signal_exports),
        (mongoz.exceptions, exception_exports),
    )

    for module, exports in modules_and_exports:
        assert len(exports) == len(set(exports))
        assert all(hasattr(module, name) for name in exports)


async def test_connection_wrappers_have_explicit_native_escape_hatches() -> None:
    database = client.get_database("test_db")
    collection = database.get_collection("records")

    assert isinstance(collection, Collection)
    assert database.driver is database._db
    assert collection.driver is collection._collection
    assert client.driver["test_db"] is not None


async def test_queryset_protocol_is_public_and_runtime_check_free() -> None:
    assert QuerySetProtocol.__module__ == "mongoz.protocols.queryset"
