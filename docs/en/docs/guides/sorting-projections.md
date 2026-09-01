---
title: Sorting, pagination, and projections
description: Apply deterministic sort order, skip and limit pages, and Mongoz only/defer projections without shared query mutation.
---

# Sorting, pagination, and projections

Sorting, skip, limit, and projection are query state. Every builder returns an isolated clone and
async iteration preserves the complete state.

## Sorting

```python
from mongoz import Order

ordered = User.objects.sort("created_at", Order.DESCENDING)
stable = ordered.sort("id", Order.ASCENDING)
```

For stable pagination, include a deterministic tie-breaker such as the identifier. Without one,
documents with equal sort keys may move between pages as writes occur.

## Offset pagination

```python
page_size = 50
page = await User.objects.sort("id").skip(100).limit(page_size)
```

Large offsets require MongoDB to walk skipped results. For high-cardinality collections, prefer a
range predicate on an indexed stable key and remember the last value from the previous page.

## Projections

`only()` includes selected modeled fields and the identifier. `defer()` excludes selected fields.
They cannot be combined on one chain.

```python
summaries = await User.objects.only("name", "email").sort("name")
without_blob = await User.objects.defer("profile_blob")
```

A partially loaded document does not contain deferred modeled state. Saving it can synchronize the
modeled fields currently represented by that instance; use projections for reads and targeted
`update()` calls for changes unless full save semantics are intentional.

`values()` and `values_list()` return projections without hydrated document instances. They still
materialize the complete result.
