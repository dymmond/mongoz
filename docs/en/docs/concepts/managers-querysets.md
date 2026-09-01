---
title: Managers and QuerySets
description: Learn the different roles of Mongoz Manager and QuerySet and how clone-on-write query state prevents accidental cross-talk.
---

# Managers and QuerySets

`Document.objects` is a class-bound `Manager`. It understands modeled keyword filters, related-field
lookups, projections, alternate databases, aggregation-backed query execution, and creation methods.

`Document.query(...)` returns a `QuerySet`. It accepts field expressions or trusted raw query
dictionaries and provides a narrower execution surface.

```python
from mongoz import Order, Q

manager_query = User.objects.filter(active=True).sort("name")
expression_query = User.query(Q.eq(User.active, True)).sort("name")
```

## Clone-on-write state

Every builder operation returns an isolated derivation. Filter, sort, projection, skip, limit,
database, lookup, and session state do not mutate the query from which they were derived.

```python
base = User.objects.filter(active=True)
first_page = base.sort("name").limit(20)
recent = base.sort("created_at", Order.DESCENDING).limit(20)
```

Reusing `base` is safe. Evaluation also does not consume or rewrite it, so repeated evaluation
produces a fresh database operation with the same query definition.

## Evaluation

Awaiting a Manager returns a list. QuerySets use `.all()` for the same materialized shape.
`first()`, `last()`, `get()`, `get_or_none()`, `count()`, `exists()`, `values()`, and
`values_list()` express narrower contracts.

`none()` is async and returns an isolated empty query state of the same family; it does not clear a
shared manager or mutate another chain.

Async iteration streams hydrated models and preserves filters, ordering, projection, pagination,
lookups, and bound session state. See [Concurrency and streaming](../guides/concurrency-streaming.md).
