---
title: Modernization migration guide
description: Migrate older Mongoz applications to PyMongo Async, explicit Registry lifecycle, immutable queries, safe persistence and indexes, transactions, signals, and hardened raw boundaries.
---

# Modernization migration guide

Apply these changes in order so connection, query, and persistence behavior do not shift all at
once.

## 1. Replace Motor with PyMongo Async

Remove `motor` imports and dependencies. Public native types now come from
`pymongo.asynchronous`: `AsyncMongoClient`, `AsyncDatabase`, `AsyncCollection`, async cursors, and
`AsyncClientSession`.

Mongoz requires `pymongo>=4.13,<5.0`, the supported native async driver line. Keep Pydantic and
Pydantic Settings within their declared 2.x ranges. `orjson` is not a Mongoz runtime dependency.

## 2. Make Registry lifecycle explicit

Create one Registry per application lifecycle, not per request. First database use binds its client
to that event loop. Close it asynchronously during shutdown or use `async with Registry(...)` for
bounded work. `close()` is idempotent but final; remove code that reuses or expects to reopen a
closed Registry.

Imports and document declaration perform no client or index I/O. Move connectivity checks and
`registry.document_checks()` to an explicit startup hook.

## 3. Review immutable query reuse

Manager and QuerySet builders now clone state. A derived filter, sort, limit, projection, database,
or session no longer mutates its source chain. Remove workarounds that manually reconstruct base
queries and add regression tests when callers previously depended on mutation.

`none()` is async and returns an isolated empty query state. Await it; do not expect it to clear a
shared manager.

Unknown lookup operators raise `OperatorInvalid` immediately. Correct misspelled or dynamically
invented operators rather than relying on accidental field parsing.

## 4. Choose update or save semantics

Instance `update(**values)` is an atomic modeled `$set` patch and synchronizes supplied fields on
the instance. `save()` synchronizes every modeled field and can overwrite concurrent changes to
those fields. Use targeted updates for patches and save only when the instance is the intended
snapshot.

Unknown modeled update keys and ambiguous no-op instance writes are rejected. Missing acknowledged
instance update/save/delete operations raise `DocumentNotFound`. Add handling where stale instances
were previously treated as successful writes.

Modeled create/save paths serialize declared fields only. If an application intentionally persists
schemaless extra keys, move that work to an explicit native collection boundary.

## 5. Separate `get_or_create` predicates and values

Build lookup predicates on the query and pass creation-only values in `defaults`. Mongoz no longer
mixes operator structures into the inserted document. Enforce uniqueness with a MongoDB unique index
and handle native duplicate-key races according to application policy.

## 6. Migrate index startup and deletion policy

Index declaration no longer implies import-time I/O. Use `plan_indexes()` to inspect and
`check_indexes()` to execute. Missing declarations are created by default; unmanaged indexes are
retained.

Same-name specification changes require `force_drop=True`. Unmanaged deletion requires an audited
`plan_indexes(delete_unmanaged=True)` followed by `check_indexes(drop_unmanaged=True)`. Treat
`drop_indexes(force=True)` as a destructive migration, not routine startup.

## 7. Propagate sessions explicitly

Start sessions from `registry.driver`. Bind query objects with `using_session(session)` and pass
`session=` to instance writes, aggregation, bulk writes, and index operations. There is no implicit
ambient session. Use a session sequentially; do not share it across concurrent tasks.

Transaction commit/abort and native errors remain PyMongo contracts. A replica set or sharded
cluster is required.

## 8. Adopt aggregation and bulk boundaries

`Document.aggregate(pipeline, session=...)` materializes native pipeline mappings and closes its
cursor. `Document.bulk_write(requests, ordered=..., session=...)` accepts PyMongo write models and
returns `BulkWriteResult`. Both are trusted developer structures; native errors are preserved.

## 9. Correct signal receivers

Receivers must be async callables accepting keyword arguments. Registration order is dispatch
order; execution is sequential and fail-fast. Duplicate registration is ignored, cancellation is
preserved, and document classes own isolated broadcasters. Remove synchronous receivers and any
logic that depends on unordered or background execution.

## 10. Update sync and exception boundaries

`run_sync()` accepts one awaitable and executes it exactly once. Inside a thread with a running
event loop it blocks that thread while a worker thread runs the awaitable with copied context
variables. Do not use it as a non-blocking async helper.

Import public Mongoz errors from `mongoz` or `mongoz.exceptions`. Catch native PyMongo errors for
database-owned failures. `DocumentNotFound` now covers missing acknowledged instance writes as well
as exact queries.

## 11. Harden regex and raw queries

String helpers have literal semantics and escape regex metacharacters. Use `Q.pattern()` only for
an intentional raw regex. Treat dictionaries, `raw()`, raw expressions, pipelines, bulk requests,
native drivers, and `$where` as trusted-only structures. Never forward decoded request mappings.

`$where` is legacy server-side JavaScript, cannot use indexes, and is deprecated by MongoDB 8.0.
Migrate to ordinary operators or `$expr`.

## 12. Update tooling and proof

The repository's canonical type checker is `ty`, including positive and negative consumer fixtures.
Supported usage is warning-free. Run static checks, the real standalone MongoDB suite, replica-set
transaction proof, package/wheel validation, dependency audit, docs validation, and the supported
Python matrix before release.
