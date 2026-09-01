---
title: Quickstart
description: Define a Mongoz document and perform create, query, update, and delete operations with correct Registry cleanup.
---

# Quickstart

This example defines one document and exercises the complete CRUD lifecycle. It assumes MongoDB is
available at `localhost:27017`.

## Define a Registry and document

```python
from mongoz import Boolean, Document, Registry, String

registry = Registry("mongodb://localhost:27017")

class User(Document):
    name: str = String(min_length=1, max_length=80)
    email: str = String(unique=True)
    active: bool = Boolean(default=True)

    class Meta:
        registry = registry
        database = "quickstart"
```

`Meta.database` names a MongoDB database. Unless `Meta.collection` is set, Mongoz derives the
collection name from the document class. Declaring this class performs no database or index I/O.

## Create and query

```python
async def use_users() -> None:
    async with registry:
        await User.create_indexes()

        created = await User.objects.create(
            name="Ada Lovelace",
            email="ada@example.com",
        )

        by_id = await User.objects.get(id=created.id)
        matches = await User.objects.filter(active=True).sort("name")

        assert by_id.email == "ada@example.com"
        assert matches[0].name == "Ada Lovelace"
```

Awaiting a `Manager` materializes its current query as a list. `get()` instead enforces exactly one
result and raises `DocumentNotFound` or `MultipleDocumentsReturned` when that contract is not met.

## Update and delete

```python
async def change_user(user: User) -> None:
    await user.update(name="Augusta Ada King")
    await user.delete()
```

`update()` applies an atomic patch and synchronizes the changed modeled fields on the instance.
`save()` has different full-modeled-field synchronization semantics; choose deliberately and see
[Updates and persistence](../guides/persistence.md).

## Run from synchronous code

Prefer an async application entry point. For a synchronous boundary, `run_sync()` executes one
awaitable exactly once. If called from a thread that already has a running event loop, it blocks
that thread while the awaitable runs in a worker thread.

```python
from mongoz import run_sync

run_sync(use_users())
```

Continue with the [CRUD tutorial](../tutorials/crud.md) or learn why
[Registry lifecycle](lifecycle.md) belongs to the application.
