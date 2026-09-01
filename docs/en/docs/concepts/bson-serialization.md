---
title: BSON and serialization
description: Understand how Mongoz maps Pydantic models to BSON, handles ObjectId and Decimal128, and exposes native PyMongo boundaries.
---

# BSON and serialization

Mongoz validates Python values with Pydantic, then produces MongoDB-compatible mappings for modeled
persistence. MongoDB and PyMongo remain authoritative for BSON encoding rules and server limits.

## Identity and aliases

The public document identifier is normally `id`; MongoDB stores it as `_id`. Mongoz accepts string
or BSON `ObjectId` values on supported identifier queries and raises `InvalidObjectIdError` for
Mongoz-owned conversion failures.

Field aliases affect stored keys. Use the declared model field in ordinary application code and let
the model own its mapping.

## BSON-specific values

Mongoz includes `ObjectId`, `NullableObjectId`, `Decimal`, `Binary`, `Date`, `DateTime`, `Time`, and
`UUID` field factories. Decimal values use MongoDB `Decimal128` conversion at the persistence
boundary while remaining Python `Decimal` values in the modeled interface.

## Serialization boundaries

`model_dump()` is the Pydantic-facing representation. Database writes use Mongoz's persistence
serialization, which handles aliases, modeled fields, references, embedded documents, and BSON
values. Do not treat arbitrary `model_dump()` output as an authorization-safe request payload.

For raw BSON mappings, aggregation pipelines, cursor batch control, collection options, or a driver
feature not modeled by Mongoz, use the native collection:

```python
native = User.get_collection().driver
document = await native.find_one({"email": "ada@example.com"})
```

Raw mappings are trusted developer interfaces. Validate and authorize untrusted inputs before they
reach them.
