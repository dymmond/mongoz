---
title: Concepts
description: Understand the canonical document, query, connection, validation, and native-driver boundaries in Mongoz.
---

# Concepts

Mongoz is easiest to reason about as four connected owners:

1. A [Registry](registry-boundaries.md) owns one native async client and exposes databases and collections.
2. [Documents](documents.md) declare modeled BSON data with [fields and validation](fields-validation.md).
3. [Managers and QuerySets](managers-querysets.md) build isolated query state and execute database operations.
4. [BSON and serialization](bson-serialization.md) define the boundary between modeled values and native MongoDB data.

These layers cooperate without reconstructing each other's truth. MongoDB still owns stored data
and server behavior; PyMongo still owns driver lifecycle and native database semantics.
