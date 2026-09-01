---
title: Performance
description: Use Mongoz efficiently through client reuse, indexed queries, streaming, bounded result shapes, and evidence-based benchmark interpretation.
---

# Performance

Database topology, indexes, network latency, result cardinality, BSON payloads, and application work
usually dominate end-to-end latency. Optimize with evidence and keep driver/network time separate
from Python-side ODM overhead.

## Durable practices

- Reuse one Registry for the application lifecycle so PyMongo can pool connections.
- Inspect MongoDB query plans and create indexes for real predicates and sort order.
- Prefer `count()`, `exists()`, projections, and native bounded write results over materializing documents
  that the caller will discard.
- Stream large reads and close early-exit iterators.
- Avoid logging or tracing complete result documents on hot paths.
- Use native collection operations when a high-level Mongoz method necessarily returns hydrated
  documents but the application needs only a driver result.

## Maintained evidence

The repository's CodSpeed suite measures fixed Python-side operations on Python 3.13 with 20 warmup
rounds and 100 measured rounds. It covers model construction, serialization, hydration, persistence
payloads, expression compilation, and query cloning. These are regression checks, not cross-ODM
marketing benchmarks.

`benchmarks/database.py` compares raw PyMongo and Mongoz end-to-end groups against a fixed
standalone dataset. It is informational because network and server variance are material. Reproduce
a suspicious result, then profile the owning layer before claiming an optimization.

Do not claim “zero overhead,” “fastest,” or topology-independent performance. State workload,
runtime, dataset, indexes, warmups, repeats, and variance with any result.
