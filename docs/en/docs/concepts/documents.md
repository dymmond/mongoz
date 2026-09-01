---
title: Documents
description: Learn how Mongoz documents map typed Python models to MongoDB collections and how document metadata controls that mapping.
---

# Documents

A `Document` is a Pydantic model connected to one Registry, database, and collection. Its declared
fields are the canonical modeled persistence surface.

```python
from mongoz import Document, Integer, Registry, String

registry = Registry("mongodb://localhost:27017")

class Movie(Document):
    title: str = String(min_length=1)
    year: int = Integer(minimum=1888)

    class Meta:
        registry = registry
        database = "catalog"
        collection = "movies"
```

## Metadata

| `Meta` option | Meaning |
| --- | --- |
| `registry` | Registry that owns the document's client and database access. |
| `database` | MongoDB database name. |
| `collection` | Optional MongoDB collection name; Mongoz otherwise derives one. |
| `indexes` | Declared `Index` objects used by planning and reconciliation. |
| `abstract` | Marks a base document that provides fields but cannot perform database operations. |
| `autogenerate_index` | Compatibility metadata used by the multiple-database index helpers. It does not trigger import-time I/O. |

The correct MongoDB term is **collection**, not table. Older `tablename` examples are migration
history, not current vocabulary.

## Modeled and schemaless data

MongoDB documents may contain keys that a model does not declare. Mongoz can hydrate compatible
schemaless documents, but modeled create and save paths serialize declared fields only. Unknown
hydrated keys are not silently written back. Raw PyMongo access remains available when intentionally
preserving arbitrary shapes is the requirement.

## Identity and instance operations

Mongoz maps the public `id` field to MongoDB `_id`. Instances support `create()`, `update()`,
`save()`, and `delete()`, with optional explicit `session=` propagation. Missing acknowledged
instance updates, saves, or deletes raise `DocumentNotFound` rather than reporting false success.

## Abstract documents and inheritance

Abstract documents share field declarations without owning a database collection. Concrete child
documents receive their own metadata and signal namespace. See
[Inheritance and relations](../guides/inheritance-relations.md) for patterns and constraints.
