---
title: Fields and validation
description: Understand Mongoz field declarations, Pydantic validation, defaults, aliases, indexes, and serialization constraints.
---

# Fields and validation

Mongoz field factories create Pydantic field definitions with MongoDB-oriented metadata. Python
annotations remain the source of the model's public value types.

```python
from datetime import datetime
from mongoz import Boolean, DateTime, Document, Integer, String

class Event(Document):
    title: str = String(min_length=1, max_length=120)
    capacity: int = Integer(minimum=1)
    published: bool = Boolean(default=False)
    created_at: datetime = DateTime(auto_now_add=True)
```

Validation occurs during model construction and modeled persistence. Field validators and Pydantic
model validators are not bypassed merely because data originated in MongoDB. Invalid modeled data
raises the applicable Pydantic or Mongoz-owned error.

## Common field options

| Option | Purpose |
| --- | --- |
| `default`, `default_factory` | Supply a value when the caller omits the field. |
| `null` | Allow a stored `None` where supported. |
| `read_only` | Document model intent; it is not an authorization boundary. |
| `index`, `unique` | Contribute index metadata; creation still requires explicit reconciliation. |
| `alias` | Map a public/model field to a stored key. |
| `min_length`, `max_length` | Bound strings, arrays, or binary values where supported. |
| `minimum`, `maximum` | Bound numeric values. |

Applications must use dedicated input models or allowlists for request authorization. A field marked
`read_only` does not stop an untrusted caller from supplying a key to a raw query or native driver
operation.

See the complete [field reference](../reference/fields.md) and
[BSON and serialization](bson-serialization.md).
