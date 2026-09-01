---
title: Public API
description: Inventory the supported top-level Mongoz public API without exposing internal implementation symbols as user contracts.
---

# Public API

This reference inventories the symbols exported by `mongoz.__all__`. Internal modules remain
implementation details unless another reference page explicitly documents them.

## Documents and connections

| Symbol | Purpose |
| --- | --- |
| `Document` | Persisted Pydantic-backed MongoDB document. |
| `EmbeddedDocument` | Validated nested document without independent persistence. |
| `Registry` | Owner of one PyMongo `AsyncMongoClient`. |
| `Database` | Wrapper around one native async database view. |
| `Collection` | Wrapper around one native async collection view. |

## Queries and indexes

| Symbol | Purpose |
| --- | --- |
| `Manager`, `QuerySet`, `QuerySetManager` | Query construction, execution, and custom manager binding. |
| `Q`, `Expression`, `SortExpression` | Explicit query and sort expressions. |
| `Index`, `IndexType`, `Order` | Index declarations and MongoDB ordering/index types. |
| `IndexPlan`, `IndexPlanEntry`, `IndexAction` | Inspectable index reconciliation result. |

## Fields

`Array`, `ArrayList`, `Binary`, `Boolean`, `Date`, `DateTime`, `Decimal`, `Double`, `Email`,
`Embed`, `ForeignKey`, `Integer`, `NullableObjectId`, `Object`, `ObjectId`, `String`, `Time`, and
`UUID` are top-level field factories or BSON-aware value types. The `fields` namespace is also
exported.

## Signals, settings, and sync bridge

| Symbol | Purpose |
| --- | --- |
| `Signal` | Async-only sequential signal receiver registry. |
| `MongozSettings`, `settings` | Settings model and lazy configured instance. |
| `run_sync` | Execute one awaitable from a synchronous boundary. |

## Exceptions

`MongozException`, `DocumentNotFound`, `MultipleDocumentsReturned`, `ImproperlyConfigured`,
`FieldDefinitionError`, `InvalidKeyError`, `InvalidObjectIdError`, `SignalError`,
`AbstractDocumentError`, `OperatorInvalid`, and `mongoz.IndexError` are public. Native database
errors remain PyMongo classes.

## Native types

Mongoz's runtime annotations expose PyMongo Async types for clients, databases, collections,
cursors, and sessions. Motor types are not part of the supported API.
