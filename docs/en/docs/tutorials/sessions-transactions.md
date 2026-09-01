---
title: Sessions and transactions
description: Use PyMongo Async sessions and transactions with Mongoz while propagating one session sequentially to every operation.
---

# Sessions and transactions

PyMongo owns session and transaction lifecycle. Mongoz provides explicit propagation through
`using_session()` and `session=` parameters; there is no ambient session.

Transactions require a replica set or sharded cluster. They do not work on a standalone server.

## Transfer between documents

```python
{!> docs_src/examples/transactions.py !}
```

The included example uses a `User` document. The bound Manager propagates the session to its query and create operations. Instance operations
are separate objects, so pass `session=session` explicitly to `create()`, `update()`, `save()`, or
`delete()`.

Aggregation, bulk writes, and index operations also accept a session where PyMongo supports one:

```python
summary = await Account.aggregate(pipeline, session=session)
result = await Account.bulk_write(requests, session=session)
```

## Failure behavior

Normal exit commits; an exception aborts. Native PyMongo transaction and write errors propagate.
Retrying a whole transaction is an application decision because only the application knows whether
non-database side effects are idempotent.

One session must be used sequentially. Do not pass it into `asyncio.gather()` or multiple concurrent
tasks. After an abort, start a new transaction instead of reusing the ended transaction context.

Signals run inside the calling operation's task and can fail after a database write has completed.
Do not blindly retry a write because a post-write signal receiver failed.
