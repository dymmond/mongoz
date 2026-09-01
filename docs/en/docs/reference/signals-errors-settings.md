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

Mongoz-owned exceptions accept an optional `detail=` keyword, which is appended to positional
message fragments. `DocumentNotFound()` and `MultipleDocumentsReturned()` use their documented
default messages when constructed without arguments.

```python
from mongoz.exceptions import DocumentNotFound

try:
    user = await User.query(User.email == "missing@example.com").get()
except DocumentNotFound as exc:
    print(exc)  # Document not found.
```

Catch native PyMongo exceptions separately when using writes, transactions, or native driver
escape hatches; Mongoz deliberately preserves those concrete error types.

## Settings

`MongozSettings` defines identifier aliases, relation lookup prefix, query operator mapping, and
shell defaults. `mongoz.settings` is loaded lazily. Set `MONGOZ_SETTINGS_MODULE` to a dotted import path
for a `MongozSettings` subclass when custom global settings are required.

Invalid imports, wrong base classes, invalid Pydantic values, and uppercase setting names raise
`ImproperlyConfigured`. Validation errors retain their cause while hiding input values. String and
repr rendering of the lazy settings proxy exposes only its state or configured class name. Use
Pydantic `SecretStr` or `SecretBytes` for application-defined secret fields as an additional
model-level safeguard.

Custom query operators should be explicit application policy. Prefer ordinary field expressions
and raw native escape hatches over globally changing familiar operator meaning.
