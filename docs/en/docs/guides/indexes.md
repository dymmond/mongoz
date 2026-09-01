---
title: Index planning and reconciliation
description: Inspect Mongoz index plans, create missing declarations, resolve conflicts, and opt into destructive reconciliation only when reviewed.
---

# Index planning and reconciliation

Index metadata on a document is desired state, not authorization to mutate the server during import.
Use an explicit inspect → review → execute workflow.

## Declare

```python
from mongoz import Index, Order

class Meta:
    indexes = [
        Index("email", name="user_email_unique", unique=True),
        Index(
            keys=[("tenant_id", Order.ASCENDING), ("created_at", Order.DESCENDING)],
            name="tenant_created",
        ),
    ]
```

## Plan

```python
plan = await User.plan_indexes()
```

| Action | Meaning |
| --- | --- |
| `already_correct` | Name and specification already match. |
| `create` | A declaration is missing. |
| `recreate` | The same declared name has a different specification. |
| `retain_unmanaged` | An undeclared server index remains untouched. |
| `candidate_for_deletion` | An unmanaged index would be deleted under an explicit policy. |
| `name_conflict` | Equivalent or conflicting state needs a human ownership decision. |

Planning performs server inspection but no mutation.

## Execute

```python
await User.check_indexes()
```

The default creates missing declarations and retains `_id_` and unmanaged indexes. A same-name
specification change stops unless `force_drop=True` explicitly authorizes recreation. To audit
unmanaged cleanup, first call `plan_indexes(delete_unmanaged=True)`; only
`check_indexes(drop_unmanaged=True)` authorizes those deletions.

`drop_index(name)` drops one declared index. `drop_indexes()` drops declared indexes; passing
`force=True` asks PyMongo to drop all non-`_id_` indexes and is a destructive migration operation.

!!! danger "Ownership before deletion"
    Removing an index from model metadata does not prove Mongoz owns the server index or that it is
    unused. Review production query plans and migration history before destructive reconciliation.
