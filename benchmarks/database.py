"""Repeatable standalone MongoDB benchmark for driver and ODM-facing latency.

Run with a local standalone server and Python 3.13::

    hatch run matrix.py3.13:python benchmarks/database.py

The report keeps raw PyMongo operations separate from Mongoz end-to-end operations.
It is informational release evidence, not a cross-project marketing benchmark.
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import statistics
import sys
import time
from collections.abc import Awaitable, Callable
from typing import Any

import pymongo
from pymongo import AsyncMongoClient

import mongoz

DATABASE_URI = os.environ.get(
    "DATABASE_URI", "mongodb://root:mongoadmin@localhost:27017/?authSource=admin"
)
DATABASE_NAME = "mongoz_benchmark"
COLLECTION_NAME = "records"
DATASET_SIZE = 1_000
WARMUPS = 5
REPEATS = 9

registry = mongoz.Registry(DATABASE_URI)


class BenchmarkRecord(mongoz.Document):
    seq: int = mongoz.Integer()
    name: str = mongoz.String()
    group: int = mongoz.Integer()
    payload: str = mongoz.String()

    class Meta:
        registry = registry
        database = DATABASE_NAME
        collection = COLLECTION_NAME


async def measure(operation: Callable[[], Awaitable[Any]]) -> dict[str, float]:
    """Measure one fixed async workload after warmup and summarize milliseconds."""
    for _ in range(WARMUPS):
        await operation()
    samples = []
    for _ in range(REPEATS):
        started = time.perf_counter_ns()
        await operation()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    ordered = sorted(samples)
    return {
        "median_ms": round(statistics.median(samples), 4),
        "min_ms": round(min(samples), 4),
        "max_ms": round(max(samples), 4),
        "p95_ms": round(ordered[-1], 4),
        "rsd_percent": round(statistics.stdev(samples) / statistics.mean(samples) * 100, 2),
    }


async def main() -> None:
    """Create the fixed dataset, run operations, and emit a machine-readable report."""
    client: AsyncMongoClient[dict[str, Any]] = registry.driver
    database = client[DATABASE_NAME]
    collection = database[COLLECTION_NAME]
    await collection.drop()
    await collection.insert_many(
        [
            {
                "seq": index,
                "name": f"record-{index}",
                "group": index % 10,
                "payload": "x" * 128,
            }
            for index in range(DATASET_SIZE)
        ]
    )
    await collection.create_index("seq", unique=True)

    async def raw_lookup() -> None:
        await collection.find_one({"seq": 500})

    async def mongoz_lookup() -> None:
        await BenchmarkRecord.objects.filter(seq=500).get()

    async def raw_projected_lookup() -> None:
        await collection.find_one({"seq": 500}, {"_id": 1, "seq": 1, "name": 1})

    async def mongoz_projected_lookup() -> None:
        await BenchmarkRecord.objects.filter(seq=500).only("seq", "name").get()

    async def raw_materialize_100() -> None:
        await collection.find({"group": 5}).sort("seq").to_list(length=100)

    async def mongoz_materialize_100() -> None:
        await BenchmarkRecord.objects.filter(group=5).sort("seq").limit(100)

    async def raw_stream_100() -> None:
        async for _ in collection.find({"group": 5}).sort("seq").limit(100):
            pass

    async def mongoz_stream_100() -> None:
        async for _ in BenchmarkRecord.objects.filter(group=5).sort("seq").limit(100):
            pass

    results = {
        "raw_driver": {
            "single_lookup": await measure(raw_lookup),
            "projected_lookup": await measure(raw_projected_lookup),
            "materialize_100": await measure(raw_materialize_100),
            "stream_100": await measure(raw_stream_100),
        },
        "mongoz_end_to_end": {
            "single_lookup": await measure(mongoz_lookup),
            "projected_lookup": await measure(mongoz_projected_lookup),
            "materialize_100": await measure(mongoz_materialize_100),
            "stream_100": await measure(mongoz_stream_100),
        },
    }
    server = await database.command("buildInfo")
    report = {
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pymongo": pymongo.version,
            "mongodb": server["version"],
            "topology": "standalone",
            "dataset_size": DATASET_SIZE,
            "warmups": WARMUPS,
            "repeats": REPEATS,
        },
        "results": results,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    await collection.drop()
    await registry.close()


if __name__ == "__main__":
    asyncio.run(main())
