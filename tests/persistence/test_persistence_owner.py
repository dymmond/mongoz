import asyncio
from typing import AsyncGenerator

import pytest
from bson import ObjectId
from pydantic import field_validator

import mongoz
from mongoz import Document
from mongoz.exceptions import DocumentNotFound, InvalidKeyError
from tests.conftest import client

pytestmark = pytest.mark.anyio


class BaseRecord(Document):
    tenant: str = mongoz.String()

    class Meta:
        abstract = True
        registry = client
        database = "test_db"


class PersistenceRecord(BaseRecord):
    title: str = mongoz.String(name="stored_title", min_length=2)
    count: int = mongoz.Integer()
    enabled: bool = mongoz.Boolean(default=True)
    note: str = mongoz.String(default="note")

    class Meta:
        collection = "persistence_owner"

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str) -> str:
        return value.strip()


@pytest.fixture(autouse=True)
async def prepare_database() -> AsyncGenerator[None, None]:
    default = client.driver["test_db"]
    alternate = client.driver["test_persistence_alternate"]
    await default.drop_collection("persistence_owner")
    await alternate.drop_collection("persistence_owner")
    yield
    await default.drop_collection("persistence_owner")
    await alternate.drop_collection("persistence_owner")


async def test_instance_update_is_a_validated_atomic_patch() -> None:
    record = await PersistenceRecord(
        tenant="one", title="initial", count=4, note="original"
    ).create()
    stale = await PersistenceRecord.objects.get()
    await PersistenceRecord.get_collection().update_one(
        {"_id": record.id}, {"$set": {"note": "external"}}
    )

    await stale.update(count=0, enabled=False, title="patched")

    stored = await PersistenceRecord.get_collection().find_one({"_id": record.id})
    assert stored is not None
    assert stored["note"] == "external"
    assert stored["count"] == 0
    assert stored["enabled"] is False
    assert stored["stored_title"] == "patched"
    assert "title" not in stored


async def test_update_accepts_inherited_fields_and_rejects_unknown_or_invalid_fields() -> None:
    record = await PersistenceRecord(tenant="one", title="initial", count=1, note="").create()

    await record.update(tenant="two", note="  normalized  ")
    assert record.tenant == "two"
    assert record.note == "normalized"

    with pytest.raises(InvalidKeyError):
        await record.update(unknown="ignored")
    with pytest.raises(ValueError):
        await record.update(title="x")


async def test_save_explicitly_synchronizes_all_model_fields() -> None:
    record = await PersistenceRecord(
        tenant="one", title="initial", count=1, note="original"
    ).create()
    stale = await PersistenceRecord.objects.get()
    await PersistenceRecord.get_collection().update_one(
        {"_id": record.id}, {"$set": {"note": "external"}}
    )

    stale.count = 2
    await stale.save()

    stored = await PersistenceRecord.get_collection().find_one({"_id": record.id})
    assert stored is not None
    assert stored["count"] == 2
    assert stored["note"] == "original"


async def test_acknowledged_instance_writes_reject_missing_persisted_ids() -> None:
    record = PersistenceRecord(tenant="one", title="missing", count=1)
    record.id = ObjectId()

    with pytest.raises(DocumentNotFound):
        await record.update(count=2)
    with pytest.raises(DocumentNotFound):
        await record.save()
    with pytest.raises(DocumentNotFound):
        await record.delete()


async def test_update_many_returns_only_the_original_targets_without_mutating_filter() -> None:
    await PersistenceRecord(tenant="one", title="target", count=1, note="one").create()
    unrelated = await PersistenceRecord(tenant="two", title="other", count=0, note="two").create()
    query = PersistenceRecord.objects.filter(count=1)

    updated = await query.update_many(count=0)

    assert len(updated) == 1
    assert updated[0].title == "target"
    assert updated[0].id != unrelated.id
    assert len(await query) == 0


async def test_get_or_create_keeps_operator_predicates_out_of_creation_values() -> None:
    record = await PersistenceRecord.objects.filter(count__gte=3).get_or_create(
        {"tenant": "one", "title": "operator", "count": 4, "note": "created"}
    )

    assert record.count == 4
    assert await PersistenceRecord.objects.count() == 1

    logical = await PersistenceRecord.objects.raw(
        mongoz.Q.nor_(PersistenceRecord.count < 100)
    ).get_or_create({"tenant": "two", "title": "logical", "count": 101, "note": "created"})
    assert logical.title == "logical"

    with pytest.raises(InvalidKeyError, match="unknown"):
        await PersistenceRecord.objects.raw({"unknown": "value"}).get_or_create(
            {"tenant": "three", "title": "invalid", "count": 1}
        )


async def test_concurrent_get_or_create_uses_one_unique_document() -> None:
    await PersistenceRecord.get_collection().create_index("stored_title", unique=True)

    async def create() -> PersistenceRecord:
        return await PersistenceRecord.objects.filter(title="shared").get_or_create(
            {"tenant": "one", "count": 1}
        )

    records = await asyncio.gather(*(create() for _ in range(8)))

    assert len({record.id for record in records}) == 1
    assert await PersistenceRecord.objects.count() == 1
    assert (await PersistenceRecord.objects.filter(title="shared").get()).id == records[0].id
    stored = await PersistenceRecord.get_collection().find_one({"_id": records[0].id})
    assert stored is not None
    assert stored["stored_title"] == "shared"
    assert "title" not in stored


async def test_collection_routing_is_instance_local_under_concurrency() -> None:
    default = await PersistenceRecord(tenant="default", title="default", count=1).create()
    alternate = await PersistenceRecord.objects.using("test_persistence_alternate").create(
        tenant="alternate", title="alternate", count=1
    )

    await asyncio.gather(default.update(count=2), alternate.update(count=3))

    default_stored = await PersistenceRecord.get_collection().find_one({"_id": default.id})
    alternate_collection = client.get_database("test_persistence_alternate").get_collection(
        "persistence_owner"
    )
    alternate_stored = await alternate_collection._collection.find_one({"_id": alternate.id})
    assert default_stored is not None and default_stored["count"] == 2
    assert alternate_stored is not None and alternate_stored["count"] == 3
    assert await PersistenceRecord.get_collection().find_one({"_id": alternate.id}) is None
