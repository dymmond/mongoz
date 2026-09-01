---
title: Aggregation and bulk writes
description: Run trusted MongoDB aggregation pipelines and PyMongo bulk-write requests through a Mongoz document collection.
---

# Aggregation and bulk writes

Aggregation pipelines and bulk requests are native MongoDB/PyMongo structures. Mongoz selects the
document's collection, propagates an optional session, closes aggregation cursors, and preserves
native results and errors. It does not sanitize pipeline operators.

## Aggregation

```python
pipeline = [
    {"$match": {"status": "paid"}},
    {"$group": {"_id": "$customer_id", "total": {"$sum": "$amount"}}},
    {"$sort": {"total": -1}},
]

totals = await Invoice.aggregate(pipeline)
```

`aggregate()` materializes the complete result as a list of mappings. For unbounded pipelines or
fine-grained cursor options, use `Invoice.get_collection().aggregate(...)` and own cursor cleanup.

## Bulk writes

```python
from pymongo import DeleteOne, UpdateOne

result = await Invoice.bulk_write(
    [
        UpdateOne({"status": "draft"}, {"$set": {"status": "expired"}}),
        DeleteOne({"status": "cancelled", "retention_complete": True}),
    ],
    ordered=True,
)

print(result.modified_count, result.deleted_count)
```

`bulk_write()` accepts PyMongo collection-level write models and returns `BulkWriteResult`.
`BulkWriteError`, duplicate-key failures, and write-concern failures propagate unchanged.

!!! warning "Trusted structures"
    Never forward a decoded request mapping into an aggregation stage, raw filter, update document,
    or bulk-write model. Build allowed operations in application code and enforce tenant predicates
    independently.

Both methods accept `session=`. The [sessions and transactions tutorial](sessions-transactions.md)
shows the required propagation pattern.
