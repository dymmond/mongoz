---
title: Updates and persistence
description: Choose Mongoz atomic patch, full modeled save, create, and delete semantics while handling validation, unknown keys, sessions, and missing writes.
---

# Updates and persistence

Mongoz separates a selected-field atomic patch from a full modeled-field synchronization.

## `update()` is a patch

```python
await user.update(display_name="Ada")
```

Instance `update()` validates supplied modeled keys, sends one `$set`, and synchronizes those fields
on the instance. Manager and QuerySet `update()`/`update_many()` patch every match and return the
hydrated documents that still match the updated values.

Unknown update keys are rejected. An empty instance patch is an explicit no-op that returns the
same instance; a missing acknowledged instance match raises `DocumentNotFound`.

## `save()` synchronizes the model

```python
user.display_name = "Ada Lovelace"
await user.save()
```

`save()` writes every modeled field represented by the instance. It can overwrite concurrent
changes to those fields, so use it when the instance is the intended canonical snapshot. If the
instance has no identifier, `save()` creates it.

Schemaless unknown keys encountered during hydration are not silently persisted by modeled save.
Use a native collection operation when arbitrary unmodeled keys are intentionally owned.

## Sessions and failures

Instance methods accept `session=`. Manager and QuerySet operations propagate a session bound with
`using_session()`.

Native duplicate-key, validation, write-concern, timeout, and topology errors remain native PyMongo
or Pydantic errors. Mongoz-owned key and missing-document contracts use public exceptions documented in
[Signals, exceptions, and settings](../reference/signals-errors-settings.md).

Signals are awaited around modeled instance writes. A post-write receiver can fail after the
database operation committed; recovery must distinguish the signal failure from the write outcome.
