from typing import AsyncGenerator

import pytest

import mongoz
from mongoz import Document, Index, IndexAction, IndexType, Order
from mongoz.exceptions import IndexError as MongozIndexError
from tests.conftest import client

pytestmark = pytest.mark.anyio


class SafeIndexDocument(Document):
    email: str = mongoz.String()
    status: str = mongoz.String()
    expires_at: int = mongoz.Integer()
    title: str = mongoz.String()

    class Meta:
        registry = client
        database = "test_db"
        collection = "safe_index_owner"
        indexes = [
            Index("email", unique=True),
            Index(
                keys=[("status", Order.ASCENDING), ("expires_at", Order.DESCENDING)],
                name="status_expiry",
                partialFilterExpression={"status": "active"},
            ),
            Index("expires_at", name="ttl_expiry", expireAfterSeconds=60),
            Index(keys=[("title", IndexType.TEXT)], name="title_search"),
        ]


class RenamedIndexDocument(Document):
    value: str = mongoz.String()

    class Meta:
        registry = client
        database = "test_db"
        collection = "renamed_index_owner"
        indexes = [Index("value", name="declared_value")]


@pytest.fixture(autouse=True)
async def prepare_database() -> AsyncGenerator[None, None]:
    await client.driver["test_db"].drop_collection("safe_index_owner")
    await client.driver["test_db"].drop_collection("renamed_index_owner")
    await client.driver["test_index_alternate"].drop_collection("safe_index_owner")
    yield
    await client.driver["test_db"].drop_collection("safe_index_owner")
    await client.driver["test_db"].drop_collection("renamed_index_owner")
    await client.driver["test_index_alternate"].drop_collection("safe_index_owner")


async def test_plan_creates_missing_indexes_then_reports_exact_matches() -> None:
    plan = await SafeIndexDocument.plan_indexes()
    assert [entry.name for entry in plan.actions(IndexAction.CREATE)] == [
        "email",
        "status_expiry",
        "ttl_expiry",
        "title_search",
    ]
    assert plan.actions(IndexAction.RETAIN) == ()

    await SafeIndexDocument.check_indexes()
    matching = await SafeIndexDocument.plan_indexes()

    assert [entry.name for entry in matching.actions(IndexAction.CORRECT)] == [
        "email",
        "status_expiry",
        "ttl_expiry",
        "title_search",
    ]
    assert matching.actions(IndexAction.RECREATE) == ()


async def test_changed_definition_requires_explicit_same_name_recreation() -> None:
    collection = SafeIndexDocument.get_collection()
    await collection.create_index("email", name="email", unique=False)

    plan = await SafeIndexDocument.plan_indexes()
    assert [entry.name for entry in plan.actions(IndexAction.RECREATE)] == ["email"]
    with pytest.raises(MongozIndexError, match="force_drop=True"):
        await SafeIndexDocument.check_indexes()

    observed = {index["name"]: index for index in await SafeIndexDocument.list_indexes()}
    assert observed["email"].get("unique") is None

    await SafeIndexDocument.check_indexes(force_drop=True)
    observed = {index["name"]: index for index in await SafeIndexDocument.list_indexes()}
    assert observed["email"]["unique"] is True


async def test_unmanaged_and_driver_indexes_are_never_reconciliation_drop_candidates() -> None:
    collection = SafeIndexDocument.get_collection()
    await collection.create_index("status", name="manual_status")

    plan = await SafeIndexDocument.check_indexes()

    retained = {entry.name for entry in plan.actions(IndexAction.RETAIN)}
    assert retained == {"_id_", "manual_status"}
    assert {index["name"] for index in await SafeIndexDocument.list_indexes()} >= retained


async def test_alternate_collection_plan_and_execution_are_isolated() -> None:
    default = SafeIndexDocument.get_collection()
    alternate = (
        client.get_database("test_index_alternate").get_collection("safe_index_owner")._collection
    )
    await default.create_index("status", name="default_manual")

    await SafeIndexDocument.check_indexes(collection=alternate)

    default_names = {index["name"] for index in await SafeIndexDocument.list_indexes(default)}
    alternate_names = {index["name"] for index in await SafeIndexDocument.list_indexes(alternate)}
    assert "default_manual" in default_names
    assert "default_manual" not in alternate_names
    assert {index.name for index in SafeIndexDocument.meta.indexes} <= alternate_names


async def test_equivalent_specification_with_different_name_is_an_explicit_conflict() -> None:
    await RenamedIndexDocument.get_collection().create_index("value", name="manual_value")

    plan = await RenamedIndexDocument.plan_indexes()

    assert [entry.name for entry in plan.actions(IndexAction.CONFLICT)] == ["declared_value"]
    with pytest.raises(MongozIndexError, match="manual_value"):
        await RenamedIndexDocument.check_indexes(force_drop=True)
    names = {index["name"] for index in await RenamedIndexDocument.list_indexes()}
    assert names == {"_id_", "manual_value"}


async def test_index_inheritance_is_additive_and_isolated_between_siblings() -> None:
    declared = [Index("tenant", name="base_tenant")]

    class IndexedBase(Document):
        tenant: str = mongoz.String()

        class Meta:
            abstract = True
            registry = client
            database = "test_db"
            indexes = declared

    class FirstChild(IndexedBase):
        first: str = mongoz.String()

        class Meta:
            indexes = [Index("first", name="first_only")]

    class SecondChild(IndexedBase):
        second: str = mongoz.String()

        class Meta:
            indexes = [Index("second", name="second_only")]

    FirstChild.meta.indexes.pop()

    assert [index.name for index in declared] == ["base_tenant"]
    assert [index.name for index in IndexedBase.meta.indexes] == ["base_tenant"]
    assert [index.name for index in FirstChild.meta.indexes] == ["first_only"]
    assert [index.name for index in SecondChild.meta.indexes] == [
        "second_only",
        "base_tenant",
    ]
