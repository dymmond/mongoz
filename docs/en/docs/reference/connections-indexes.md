---
title: Connections and indexes
description: Reference Mongoz Registry, Database, Collection, native driver, session, and index inspection and reconciliation methods.
---

# Connections and indexes

## Registry

| Member | Contract |
| --- | --- |
| `Registry(url)` | Creates one registry-owned PyMongo `AsyncMongoClient`; no network I/O is forced. |
| `driver` | Native `AsyncMongoClient`; Registry retains lifecycle ownership. |
| `get_database(name)` | Return a `Database` wrapper. |
| `get_databases()` | Await server database names as wrappers. |
| `drop_database(database)` | Await native database deletion. |
| `address` | Awaitable property yielding the selected server address when available. |
| `host`, `port` | Parsed configured endpoint compatibility accessors. |
| `is_closed` | Whether final cleanup has occurred. |
| `close()` | Async, idempotent, final cleanup. |
| async context manager | Return Registry and close on exit. |
| `document_checks()` | Explicitly check configured document indexes. |

## Database and Collection

`Database.driver` exposes a native `AsyncDatabase`; `get_collection(name)` returns a Mongoz
`Collection`; `get_collections()` awaits server collection names. `Collection.driver` exposes a
native `AsyncCollection`. None of these wrappers owns client cleanup independently.

## Index declarations and plans

`Index(key=...)` declares one ascending key. `Index(keys=[...])` declares compound or specialized
keys with `Order` and `IndexType`. Common options include `name`, `unique`, `sparse`, and
`background`, plus supported PyMongo `IndexModel` options.

| Document method | Behavior |
| --- | --- |
| `list_indexes(session=...)` | Materialize native index specifications. |
| `plan_indexes(delete_unmanaged=False, session=...)` | Inspect and return an `IndexPlan`; no mutation. |
| `check_indexes(force_drop=False, drop_unmanaged=False, session=...)` | Execute reviewed reconciliation policy. |
| `create_index(name)` | Create one index declared in metadata. |
| `create_indexes()` | Create declared indexes. |
| `drop_index(name)` | Drop one declared index. |
| `drop_indexes(force=False)` | Drop declared indexes; force delegates broad non-`_id_` deletion. |
| multi-database variants | Apply declared create/drop operations to explicit database names. |

An equivalent specification under a different name remains a conflict because name ownership cannot
be safely inferred.
