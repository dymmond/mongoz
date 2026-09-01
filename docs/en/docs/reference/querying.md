---
title: Query methods and operators
description: Reference Mongoz Manager and QuerySet methods, result shapes, operator names, and trusted raw query boundaries.
---

# Query methods and operators

## Query builders

| Method | Manager | QuerySet | Result |
| --- | :---: | :---: | --- |
| `filter(**kwargs)` | ✓ | — | Cloned modeled filter chain. |
| `raw(*values)` | ✓ | — | Cloned trusted raw filter chain. |
| `query(*values)` | — | ✓ | Cloned expression/raw filter chain. |
| `sort(key, direction)` | ✓ | ✓ | Cloned ordered chain. |
| `skip(count)`, `limit(count)` | ✓ | ✓ | Cloned pagination state. |
| `only(*fields)`, `defer(*fields)` | ✓ | ✓ | Cloned projection state. |
| `using(database_name)` | ✓ | — | Cloned alternate-database manager. |
| `using_session(session)` | ✓ | ✓ | Cloned session-bound query. |

## Evaluation and writes

| Method | Result/contract |
| --- | --- |
| await Manager / `all()` | Materialized document list. |
| async iteration | Streaming documents with cursor cleanup. |
| `none()` | Async isolated empty query state. |
| `get()` | Exactly one or a public cardinality exception. |
| `get_or_none()` | Zero/one; multiple still raises. |
| `first()`, `last()` | One or `None`. |
| `count()`, `exists()` | Scalar. |
| `distinct_values(key)` | Materialized distinct value list. |
| `values()`, `values_list()` | Materialized projection shapes. |
| `create()`, `create_many()`, `bulk_create()` | Insert modeled documents. |
| `update()`, `update_many()`, `bulk_update()` | Atomic modeled patch and hydrated list. |
| `delete()` | Deleted count. |
| `get_or_create(defaults=...)` | Existing or atomically created document. |
| `where(condition)` | Legacy materialized `$where` result. |

## Operators

| Family | Keyword/operator names |
| --- | --- |
| Equality | `exact`, `neq` |
| Membership | `in`, `not_in` |
| Comparison | `gt`, `gte`, `lt`, `lte`, `date` |
| Literal strings | `contains`, `icontains`, `startswith`, `istartswith`, `endswith`, `iendswith` |
| Raw pattern | `pattern` / `Q.pattern()` |
| Logical composition | `Q.and_`, `Q.or_`, `Q.nor_`, `Q.not_` |
| Ordering | `asc`, `desc`, `Q.asc`, `Q.desc` |
| Existence | `Q.exists` |
| Legacy JavaScript | `where` / `.where()` |

Unknown keyword lookup operators raise `OperatorInvalid`. Membership operators require a list or
tuple. Raw patterns, dictionaries, and `$where` are trusted-only interfaces; see
[Operators and raw queries](../guides/operators.md).
