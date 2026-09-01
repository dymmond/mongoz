---
title: Embedded documents
description: Model nested MongoDB values with Mongoz EmbeddedDocument and Embed fields without creating a separate collection.
---

# Embedded documents

An `EmbeddedDocument` validates a nested value that is stored inside its parent MongoDB document.
It has no Registry, database, collection, manager, or independent persistence lifecycle.

```python
from mongoz import Document, Embed, EmbeddedDocument, Registry, String

registry = Registry("mongodb://localhost:27017")

class Address(EmbeddedDocument):
    city: str = String()
    country: str = String(min_length=2, max_length=2)

class Customer(Document):
    name: str = String()
    address: Address = Embed(Address)

    class Meta:
        registry = registry
        database = "shop"
```

Use embedded documents when the nested value belongs to the parent's aggregate and is normally read
and written with it. Use a `ForeignKey` reference when the related document has its own lifecycle or
must be shared independently. MongoDB does not enforce relational integrity for references; the
application owns deletion and consistency policy.

Nested updates follow MongoDB document semantics. For precise partial changes, use an atomic update
whose keys and values are controlled by trusted application code. For a complete modeled instance
synchronization, use `save()` and understand its behavior in
[Updates and persistence](../guides/persistence.md).
