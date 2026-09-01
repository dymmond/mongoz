---
title: Registry, database, and collection
description: Understand Mongoz connection wrappers, native PyMongo Async escape hatches, lifecycle ownership, and database selection.
---

# Registry, database, and collection

The connection hierarchy mirrors MongoDB:

```text
Registry (one AsyncMongoClient)
└── Database (one native AsyncDatabase view)
    └── Collection (one native AsyncCollection view)
```

```python
from mongoz import Collection, Database, Registry

registry = Registry("mongodb://localhost:27017")
database: Database = registry.get_database("app")
collection: Collection = database.get_collection("users")

await collection.driver.create_index("email", unique=True)
```

`registry.driver`, `database.driver`, and `collection.driver` return typed native PyMongo Async
objects. They are escape hatches, not ownership transfers: `Registry.close()` remains the only
client cleanup owner.

## Multiple databases

A document's `Meta.database` selects its default database. Derive an isolated manager for another
database with `using()`:

```python
eu_users = User.objects.using("tenant_eu")
us_users = User.objects.using("tenant_us")

await eu_users.create(name="European user")
await us_users.create(name="US user")
```

Because managers use clone-on-write state, neither derivation changes `User.objects` or the other
manager. The application still owns tenant authorization; never choose a database directly from an
unvalidated request value.

## Inspection

`await registry.get_databases()` and `await database.get_collections()` expose server state through
wrappers. `await registry.address` reports the selected server address when PyMongo has one. These
operations can perform network I/O and therefore belong inside the active lifecycle.
