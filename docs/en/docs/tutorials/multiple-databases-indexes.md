---
title: Multiple databases and indexes
description: Use Mongoz across tenant databases and inspect index reconciliation before applying safe, explicit changes.
---

# Multiple databases and indexes

This example uses one document definition across two database names. Database selection is a query
derivation; it does not rewrite document metadata.

```python
from mongoz import Document, Index, Registry, String

registry = Registry("mongodb://localhost:27017")

class Customer(Document):
    email: str = String()

    class Meta:
        registry = registry
        database = "tenant_default"
        collection = "customers"
        indexes = [Index("email", unique=True, name="customer_email_unique")]
```

## Use an alternate database

```python
tenant_a = Customer.objects.using("tenant_a")
tenant_b = Customer.objects.using("tenant_b")

await tenant_a.create(email="owner@a.example")
await tenant_b.create(email="owner@b.example")
```

Validate tenant identifiers against an application-owned allowlist. `using()` is not an
authorization system.

## Inspect before execution

```python
plan = await Customer.plan_indexes()

for entry in plan.entries:
    print(entry.action.value, entry.name)
```

Planning reads server metadata and returns `already_correct`, `create`, `recreate`,
`retain_unmanaged`, `candidate_for_deletion`, or `name_conflict` entries without changing indexes.

## Apply an explicit policy

```python
await Customer.check_indexes()
```

The default creates missing declarations and retains unmanaged indexes. A changed declaration with
the same name requires `force_drop=True`; unmanaged deletion requires `drop_unmanaged=True`. The
driver-managed `_id_` index is always retained.

For several database names, use `create_indexes_for_multiple_databases()` after reviewing the
target list. The document must already own a default `Meta.database` and `Meta.collection`.
When `autogenerate_index=True`, Mongoz also appends that default database to the supplied names.
Destructive multi-database operations deserve an application migration with an explicit audit
trail, not an import-time side effect.
