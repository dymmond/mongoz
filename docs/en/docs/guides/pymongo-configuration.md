---
title: PyMongo configuration and resilience
description: Configure Mongoz connection timeouts, retries, concerns, topology, cancellation, and native error recovery through PyMongo Async.
---

# PyMongo configuration and resilience

Mongoz passes the complete URI to PyMongo and does not create a competing timeout, retry, concern,
or topology layer.

## Timeouts

Configure bounded server selection, connection, socket, wait-queue, and operation budgets according
to deployment latency and recovery objectives:

```python
registry = Registry(
    "mongodb://db.example/app?serverSelectionTimeoutMS=5000"
    "&connectTimeoutMS=3000&socketTimeoutMS=10000"
    "&waitQueueTimeoutMS=2000&timeoutMS=15000"
)
```

For a narrower operation budget, use PyMongo's timeout context:

```python
import pymongo

with pymongo.timeout(2.5):
    user = await User.objects.get(email="user@example.com")
```

## Retries and concerns

PyMongo owns retryable reads and writes, read preference, read concern, and write concern. Configure
client defaults in the URI. For an operation-specific native collection, use
`collection.driver.with_options(...)`.

Do not blindly retry a multi-step application workflow. A write can succeed before a signal or
non-database side effect fails. Whole-transaction retries require an application-owned idempotency
policy.

## Native errors

Server-selection, timeout, duplicate-key, bulk, write-concern, and transaction errors preserve their
native `pymongo.errors` types. Catch a narrow native error only when the application has a specific
recovery decision. Mongoz-owned semantic errors use the public taxonomy in
[Signals, exceptions, and settings](../reference/signals-errors-settings.md).

## Recovery and cleanup

A failed operation does not automatically poison an open Registry; PyMongo's topology state decides
whether later operations can recover. A closed Registry is final. Cancellation propagates, cursors
are closed by Mongoz-owned materialization paths, and Registry context cleanup retains the original
body failure if cleanup also fails.
