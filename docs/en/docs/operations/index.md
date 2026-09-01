---
title: Production checklist
description: Review Mongoz lifecycle, topology, timeout, index, security, observability, capacity, and recovery decisions before production traffic.
---

# Production checklist

Use this list for a real application and deployment review.

## Lifecycle and topology

- [ ] One Registry is reused for each application lifecycle and closed during shutdown.
- [ ] The Registry is first used and closed on the same event loop.
- [ ] Imports perform no database or index I/O.
- [ ] Startup pings the intended deployment before accepting traffic.
- [ ] Transaction workloads run on a replica set or sharded cluster, not standalone MongoDB.

## Time and durability budgets

- [ ] Server-selection, connect, socket, wait-queue, and operation timeouts are bounded.
- [ ] Retryable read/write settings are understood rather than inherited accidentally.
- [ ] Read preference, read concern, and write concern match consistency and durability needs.
- [ ] Whole-workflow and transaction retries have an application-owned idempotency policy.

## Data and indexes

- [ ] High-cardinality predicates and sort order have evidence-backed indexes.
- [ ] Index plans are reviewed before execution.
- [ ] Same-name recreation and unmanaged deletion require explicit migration authorization.
- [ ] Unique-index migrations account for existing duplicate data.
- [ ] Large reads stream or use bounded projections; large writes avoid unnecessary hydration.

## Security and observability

- [ ] Connection credentials come from a secret source and never enter logs or traces.
- [ ] TLS and authentication match deployment policy.
- [ ] Raw queries, regex, pipelines, bulk writes, and native drivers receive trusted structures only.
- [ ] Tenant and authorization predicates have one canonical application owner.
- [ ] Command monitoring redacts values according to data classification.

## Recovery

- [ ] Cancellation is re-raised after application cleanup.
- [ ] Post-write signal failures are not treated as proof that the write failed.
- [ ] Operators know when to replace a closed Registry and when PyMongo can recover an open one.
- [ ] Backups, restore tests, and MongoDB operational monitoring are owned outside Mongoz.

See [Troubleshooting](troubleshooting.md) and
[PyMongo configuration and resilience](../guides/pymongo-configuration.md).
