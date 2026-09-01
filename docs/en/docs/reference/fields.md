---
title: Fields
description: Reference Mongoz field factories, Python value types, BSON representations, and commonly supported validation and index options.
---

# Fields

Declare a Python annotation and assign a Mongoz field factory. Pydantic owns model validation;
Mongoz adds persistence and query metadata.

| Field | Python-facing value | Stored/BSON role |
| --- | --- | --- |
| `String` | `str` | String; length, pattern, choices, index metadata. |
| `Email` | `str` | Email-validated string. |
| `Integer` | `int` | Integer with optional numeric bounds. |
| `Double` | `float` | Floating-point number with optional bounds. |
| `Decimal` | `decimal.Decimal` | Converted through BSON `Decimal128`. |
| `Boolean` | `bool` | Boolean. |
| `DateTime` | `datetime.datetime` | BSON datetime; supports automatic timestamps. |
| `Date` | `datetime.date` | Date-oriented validated value. |
| `Time` | `datetime.time` | Time-oriented validated value. |
| `UUID` | `uuid.UUID` | UUID value using BSON-compatible encoding. |
| `Binary` | `bytes` | Binary data with optional length bound. |
| `Object` | `dict` | JSON-like mapping. |
| `ObjectId` | BSON-compatible identifier | Required object identifier value. |
| `NullableObjectId` | identifier or `None` | Nullable identifier field. |
| `Array(T)` | `list[T]` | Typed array. |
| `ArrayList` | `list` | Dynamically typed list. |
| `Embed(T)` | embedded model | Nested `EmbeddedDocument`. |
| `ForeignKey(T)` | related identifier/document metadata | Reference to another document collection. |

## Shared options

Availability varies by field kind. Invalid combinations raise `FieldDefinitionError` or Pydantic
validation errors.

| Option | Contract |
| --- | --- |
| `default` | Default value ownership. A callable is invoked per instance. |
| `null` | Whether `None` is accepted. Keep the Python annotation compatible. |
| `alias` | Stored/model key mapping. |
| `read_only` | Model metadata only; not request authorization. |
| `index`, `unique` | Adds desired index metadata; does not perform import-time I/O. |
| `choices` | Restricts values to declared choices. |
| `min_length`, `max_length` | Bounds strings, arrays, or binary values where supported. |
| `minimum`, `maximum` | Bounds numeric values. |
| `auto_now`, `auto_now_add` | Automatic date/datetime update or creation values. |

Use `model_fields` and Pydantic schema output for programmatic introspection. Avoid relying on
private field implementation classes.
