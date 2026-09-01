"""Readiness and capability probes for Mongoz's MongoDB test topologies."""

from __future__ import annotations

import argparse
import asyncio
from typing import Any

from pymongo import AsyncMongoClient

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
    """Prove sessions plus commit and abort on the raw async driver."""
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        uri, serverSelectionTimeoutMS=5_000
    )
    database = client["mongoz_topology_smoke"]
    collection = database["transactions"]

    try:
        hello = await client.admin.command("hello")
        if not hello.get("isWritablePrimary"):
            raise RuntimeError(f"replica set has no writable primary: {hello}")

        await database.drop_collection(collection.name)
        await collection.insert_one({"state": "seed"})
        await collection.delete_many({})

        async with client.start_session() as session:
            async with await session.start_transaction():
                await collection.insert_one({"state": "committed"}, session=session)

        committed = await collection.count_documents({"state": "committed"})
        if committed != 1:
            raise RuntimeError(f"transaction commit was not visible: {committed}")

        async with client.start_session() as session:
            await session.start_transaction()
            await collection.insert_one({"state": "aborted"}, session=session)
            await session.abort_transaction()

        aborted = await collection.count_documents({"state": "aborted"})
        if aborted != 0:
            raise RuntimeError(f"aborted transaction was persisted: {aborted}")
    finally:
        await client.drop_database(database.name)
        await client.close()


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
