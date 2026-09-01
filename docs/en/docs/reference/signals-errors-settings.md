---
title: Signals, exceptions, and settings
description: Reference Mongoz signal registration, public exception taxonomy, lazy settings ownership, and native PyMongo error boundaries.
---

# Signals, exceptions, and settings

## Signals

The top-level package exports `Signal`. Decorators are available from `mongoz.core.signals`:

`pre_save`, `post_save`, `pre_update`, `post_update`, `pre_delete`, and `post_delete`.

`Signal.connect(receiver)` requires an async callable accepting keyword arguments. `disconnect()`
returns a Boolean. `send(sender=..., **kwargs)` awaits receivers sequentially in registration order.

## Public exceptions

| Exception | Meaning |
| --- | --- |
| `MongozException` | Base for Mongoz-owned semantics. |
| `DocumentNotFound` | Exact query or acknowledged instance write found no document. |
| `MultipleDocumentsReturned` | A zero/one or exact-one query matched multiple documents. |
| `ImproperlyConfigured` | Settings, metadata, or public configuration is invalid. |
| `FieldDefinitionError` | Field or field-oriented query definition is invalid. |
| `InvalidKeyError` | Identifier, update key, field, or index key is invalid. |
| `InvalidObjectIdError` | Mongoz-owned object identifier conversion failed. |
| `SignalError` | Receiver or broadcaster configuration is invalid. |
| `AbstractDocumentError` | Database work was attempted on an abstract document. |
| `OperatorInvalid` | Query operator or operand shape is invalid. |
| `mongoz.IndexError` | Index metadata or reconciliation policy is invalid. |

Native PyMongo errors—including duplicate key, bulk write, server selection, timeout, concern, and
transaction failures—are not translated.

## Settings

`MongozSettings` defines identifier aliases, relation lookup prefix, query operator mapping, and
shell defaults. `mongoz.settings` is loaded lazily. Set `MONGOZ_SETTINGS_MODULE` to a dotted import path
for a `MongozSettings` subclass when custom global settings are required.

Invalid imports, wrong base classes, invalid Pydantic values, and uppercase setting names raise
`ImproperlyConfigured` while retaining the original import or validation error as `__cause__`.

Custom query operators should be explicit application policy. Prefer ordinary field expressions
and raw native escape hatches over globally changing familiar operator meaning.
