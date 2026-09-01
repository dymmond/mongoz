---
title: Querying
description: Build immutable Mongoz Manager and QuerySet chains, evaluate exact result contracts, and use modeled or native query boundaries deliberately.
---

# Querying

Mongoz has two related query surfaces. Managers start at `Document.objects` and provide modeled
keyword filters plus create and relation-aware behavior. QuerySets start at `Document.query()` and
compose field expressions or trusted raw dictionaries.

## Manager filters

```python
active = User.objects.filter(active=True)
admins = active.filter(role="admin")
recent = active.filter(created_at__gte=cutoff)
```

Filters are ANDed. Every call returns a clone, so `active` remains reusable. Unknown lookup
operators fail immediately with `OperatorInvalid`; they are not silently treated as field names.

## Expressions

```python
from mongoz import Q

users = await User.query(
    Q.and_(Q.eq(User.active, True), User.age >= 18)
).sort("name").all()
```

Use expressions when explicit composition reads better than keyword lookups. A dictionary passed to
`query()` is a raw MongoDB structure and belongs to trusted application code.

## Result contracts

| Operation | Result |
| --- | --- |
| `await manager` / `await queryset.all()` | Materialized list of documents. |
| `first()` / `last()` | One document or `None`. |
| `get()` | Exactly one document; otherwise a public exception. |
| `get_or_none()` | Zero or one; multiple matches still raise. |
| `count()` / `exists()` | Bounded scalar query. |
| `values()` | Materialized dictionaries with selected/excluded fields. |
| `values_list()` | Materialized tuples, or scalars with one field and `flat=True`. |
| async iteration | Streaming document hydration. |

## `get_or_create()`

Put lookup predicates in the query and creation-only values in `defaults`:

```python
user = await User.objects.filter(email=email).get_or_create(
    defaults={"name": display_name, "active": True}
)
```

Mongoz separates the atomic predicate from creation values. Invalid operator structure is not
copied into the inserted document. A unique index must enforce business uniqueness under
concurrency; catch the native duplicate-key outcome according to application policy.

## Empty query state

`await query.none()` returns an isolated empty query of the same family. It does not mutate
`Document.objects`, its source chain, or another derivation.

See [Query methods and operators](../reference/querying.md) for the compact method inventory.
