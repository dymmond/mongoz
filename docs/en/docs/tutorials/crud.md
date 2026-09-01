---
title: CRUD application
description: Build a small Mongoz repository layer with validated documents, predictable single-result queries, atomic updates, and cleanup.
---

# CRUD application

This tutorial models a small task collection and wraps its database lifecycle explicitly.

## Model the document

```python
from datetime import datetime
from mongoz import Boolean, DateTime, Document, Registry, String

registry = Registry("mongodb://localhost:27017")

class Task(Document):
    title: str = String(min_length=1, max_length=160)
    completed: bool = Boolean(default=False)
    created_at: datetime = DateTime(auto_now_add=True)

    class Meta:
        registry = registry
        database = "tasks"
        collection = "tasks"
```

Document declaration is local Python work. The first awaited database operation performs server
selection and creates connections as PyMongo requires.

## Create

```python
{!> docs_src/examples/crud.py !}
```

For multiple prepared models, `Task.create_many(models)` and `Task.objects.bulk_create(models)` use
one insert-many operation and assign inserted identifiers back to the instances.

## Read

```python
from mongoz import DocumentNotFound

try:
    task = await Task.objects.get(id=task.id)
except DocumentNotFound:
    task = None

open_tasks = await Task.objects.filter(completed=False).sort("created_at")
```

Use `get_or_none()` when absence is ordinary. Both `get()` and `get_or_none()` raise
`MultipleDocumentsReturned` when more than one document matches; they do not silently select one.

## Update

```python
await task.update(completed=True)
```

Instance `update()` validates the supplied patch, issues `$set` for those modeled fields, and
synchronizes the instance. A missing acknowledged document raises `DocumentNotFound`.

To update a selected set:

```python
updated = await Task.objects.filter(completed=False).update(completed=True)
```

This high-level method returns hydrated updated documents and therefore materializes a list. Use
native `collection.driver.update_many()` when only a bounded driver result is required.

## Delete and clean up

```python
deleted_count = await task.delete()
await registry.close()
```

In an application, close from the shutdown hook. In a script, put the complete flow inside
`async with registry:`. See [Testing applications](../guides/testing.md) for isolated fixtures.
