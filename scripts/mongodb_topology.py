"""Readiness and capability probes for Mongoz's MongoDB test topologies."""

from __future__ import annotations

import argparse
import asyncio
from typing import Any

from pymongo import AsyncMongoClient
from pymongo.errors import DuplicateKeyError

import mongoz
from mongoz import Document, Registry

STANDALONE_URI = "mongodb://root:mongoadmin@localhost:27017/?authSource=admin"
REPLICA_SET_URI = "mongodb://localhost:27018/?replicaSet=mongoz-rs"


async def standalone_smoke(uri: str) -> None:
    """Prove an authenticated async client can reach standalone MongoDB."""
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        uri, serverSelectionTimeoutMS=5_000
    )
    try:
        result = await client.admin.command("ping")
        if result.get("ok") != 1.0:
            raise RuntimeError(f"standalone ping failed: {result}")
    finally:
        await client.close()


async def replica_set_smoke(uri: str) -> None:
    """Prove Mongoz session propagation, transaction commit, abort, and failure."""
    runtime_registry = Registry(uri)
    client = runtime_registry.driver

    class TransactionRecord(Document):
        status_value: str = mongoz.String(unique=True)

        class Meta:
            registry = runtime_registry
            database = "mongoz_topology_smoke"
            collection = "transactions"

    database = client[TransactionRecord.meta.database.name]

    try:
        hello = await client.admin.command("hello")
        if not hello.get("isWritablePrimary"):
            raise RuntimeError(f"replica set has no writable primary: {hello}")

        await database.drop_collection(TransactionRecord.meta.collection.name)
        await TransactionRecord.create_indexes()

        async with client.start_session() as session:
            async with await session.start_transaction():
                record = await TransactionRecord.objects.using_session(session).create(
                    status_value="draft"
                )
                record.status_value = "saved"
                await record.save(session=session)
                await (
                    TransactionRecord.objects.using_session(session)
                    .filter(status_value="saved")
                    .update_many(status_value="committed")
                )
                visible = await (
                    TransactionRecord.objects.using_session(session)
                    .filter(status_value="committed")
                    .count()
                )
                if visible != 1:
                    raise RuntimeError(f"transactional read missed Mongoz writes: {visible}")

        committed = await TransactionRecord.objects.filter(status_value="committed").count()
        if committed != 1:
            raise RuntimeError(f"transaction commit was not visible: {committed}")

        async with client.start_session() as session:
            await session.start_transaction()
            committed_record = await (
                TransactionRecord.objects.using_session(session)
                .filter(status_value="committed")
                .get()
            )
            await committed_record.delete(session=session)
            await TransactionRecord.objects.using_session(session).create(status_value="aborted")
            await session.abort_transaction()

        aborted = await TransactionRecord.objects.filter(status_value="aborted").count()
        if aborted != 0:
            raise RuntimeError(f"aborted transaction was persisted: {aborted}")
        if await TransactionRecord.objects.filter(status_value="committed").count() != 1:
            raise RuntimeError("aborted transactional delete escaped the session")

        try:
            async with client.start_session() as session:
                async with await session.start_transaction():
                    await TransactionRecord.objects.using_session(session).create(
                        status_value="rolled-back-on-error"
                    )
                    await TransactionRecord.objects.using_session(session).create(
                        status_value="committed"
                    )
        except DuplicateKeyError:
            pass
        else:
            raise RuntimeError("duplicate write did not fail inside transaction")

        failed = await TransactionRecord.objects.filter(
            status_value="rolled-back-on-error"
        ).count()
        if failed != 0:
            raise RuntimeError(f"failed transaction was not rolled back: {failed}")
    finally:
        await client.drop_database(database.name)
        await runtime_registry.close()


def main() -> None:
    """Run the selected topology probe."""
    parser = argparse.ArgumentParser()
    parser.add_argument("topology", choices=("standalone", "replica-set"))
    parser.add_argument("--uri")
    args = parser.parse_args()

    if args.topology == "standalone":
        asyncio.run(standalone_smoke(args.uri or STANDALONE_URI))
    else:
        asyncio.run(replica_set_smoke(args.uri or REPLICA_SET_URI))


if __name__ == "__main__":
    main()
