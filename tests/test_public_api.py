from collections.abc import AsyncGenerator

import pytest
from bson import ObjectId

import mongoz
from mongoz import Collection
from mongoz.core.db import documents, fields, querysets
from mongoz.core.signals import __all__ as signal_exports
from mongoz.exceptions import __all__ as exception_exports
from mongoz.protocols import QuerySetProtocol
from scripts import pytest_warning_policy
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
    assert client.driver["test_db"] == database.driver


async def test_queryset_protocol_is_public_and_runtime_check_free() -> None:
    assert QuerySetProtocol.__module__ == "mongoz.protocols.queryset"
    assert QuerySetProtocol._is_runtime_protocol is False


async def test_explicit_pydantic_aliases_are_preserved() -> None:
    class AliasedDocument(mongoz.Document):
        label: str = mongoz.String(
            alias="stored_label",
            validation_alias="input_label",
            serialization_alias="output_label",
        )

        class Meta:
            registry = client
            database = "test_db"

    field = AliasedDocument.model_fields["label"]
    document = AliasedDocument(input_label="value")

    assert field.validation_alias == "input_label"
    assert field.serialization_alias == "output_label"
    assert document.label == "value"


async def test_row_hydration_prioritizes_mongo_id_and_exact_lookup_fields() -> None:
    class RowDocument(mongoz.Document):
        name: str = mongoz.String()
        lookup_on_notes: str = mongoz.String()

        class Meta:
            registry = client
            database = "test_db"

    mongo_id = ObjectId()
    row = RowDocument.from_row(
        {"_id": mongo_id, "id": ObjectId(), "name": "Ada", "lookup_on_notes": "ordinary"}
    )

    assert row.id == mongo_id
    assert row.lookup_on_notes == "ordinary"


async def test_warning_policy_does_not_clear_configuration_time_warnings() -> None:
    pytest_warning_policy.warning_counts.clear()

    class RecordedWarning:
        category = UserWarning

    pytest_warning_policy.pytest_warning_recorded(RecordedWarning(), "config", "", None)

    assert pytest_warning_policy.warning_counts["builtins.UserWarning"] == 1
    assert not hasattr(pytest_warning_policy, "pytest_sessionstart")
    pytest_warning_policy.pytest_unconfigure(object())  # type: ignore[arg-type]
    assert not pytest_warning_policy.warning_counts
