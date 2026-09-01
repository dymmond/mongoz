---
title: Inheritance and relations
description: Share Mongoz document fields through abstract inheritance and model embedded or referenced data without assuming relational database guarantees.
---

# Inheritance and relations

## Abstract inheritance

Use an abstract document for shared modeled fields. It has no operable collection of its own.

```python
from datetime import datetime
from mongoz import DateTime, Document

class Timestamped(Document):
    created_at: datetime = DateTime(auto_now_add=True)

    class Meta:
        abstract = True
```

Concrete children provide Registry/database metadata and receive independent collection and signal
ownership. Attempting a database operation on an abstract document raises `AbstractDocumentError`.

## Embedded values

Use `EmbeddedDocument` and `Embed` when nested data belongs to the parent lifecycle. The nested
value is stored in the same BSON document and has no manager or collection.

## References

Use `ForeignKey(RelatedDocument)` when the related value has its own collection lifecycle. Mongoz
stores the referenced identifier and can build relation-aware lookups for supported manager filters.

MongoDB does not automatically enforce foreign-key integrity, cascades, or cross-document
authorization. The application owns deletion policy and consistency. Use a transaction when a
multi-document invariant must be atomic and the deployment topology supports it.

Avoid using relational terms such as table or join as the canonical mental model. A `$lookup` is a
MongoDB aggregation stage over collections and may have different performance characteristics from
a relational join.
