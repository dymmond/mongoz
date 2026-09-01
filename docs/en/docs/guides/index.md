---
title: Guides
description: Focused Mongoz guides for queries, persistence, indexes, signals, concurrency, performance, security, testing, and PyMongo configuration.
---

# Guides

Use these pages when you already understand the document and Registry model and need one focused
answer.

| Goal | Guide |
| --- | --- |
| Build and evaluate modeled queries | [Querying](querying.md) |
| Choose safe operators and raw escape hatches | [Operators and raw queries](operators.md) |
| Control ordering, pages, and returned fields | [Sorting, pagination, and projections](sorting-projections.md) |
| Choose atomic `update()` or modeled `save()` | [Updates and persistence](persistence.md) |
| Reconcile indexes without accidental deletion | [Index planning](indexes.md) |
| Model shared fields, nesting, and references | [Inheritance and relations](inheritance-relations.md) |
| Register deterministic async receivers | [Signals](signals.md) |
| Isolate database state and lifecycle in tests | [Testing applications](testing.md) |
| Stream results and handle cancellation | [Concurrency and streaming](concurrency-streaming.md) |
| Measure without making unsupported claims | [Performance](performance.md) |
| Protect raw boundaries and secrets | [Security](security.md) |
| Configure native timeouts, retries, and concerns | [PyMongo configuration](pymongo-configuration.md) |
