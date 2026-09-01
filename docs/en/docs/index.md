---
title: Mongoz
description: Mongoz is a typed asynchronous MongoDB ODM for Python, built on PyMongo Async with explicit lifecycle, query, index, and transaction contracts.
hide:
  - toc
---

<section class="mongoz-hero">
  <div class="mongoz-hero__copy">
    <span class="mongoz-kicker">Async MongoDB ODM for Python</span>
    <h1>Model clearly.<br><span>Query without surprises.</span></h1>
    <p>
      Mongoz brings typed documents, immutable query building, deliberate index management,
      and native PyMongo Async boundaries into one focused data layer.
    </p>
    <div class="mongoz-actions">
      <a class="mongoz-button mongoz-button--primary" href="start/quickstart/">Build your first document</a>
      <a class="mongoz-button" href="migration/modernization/">Upgrade from older Mongoz</a>
    </div>
    <div class="mongoz-install" aria-label="Install Mongoz">
      <code>pip install mongoz</code>
    </div>
  </div>
  <div class="mongoz-hero__example" aria-label="Mongoz document example">
```python
from mongoz import Document, Registry, String

registry = Registry("mongodb://localhost:27017")

class User(Document):
    name: str = String(min_length=1, max_length=80)
    email: str = String(unique=True)

    class Meta:
        registry = registry
        database = "app"

async with registry:
    user = await User.objects.create(
        name="Ada",
        email="ada@example.com",
    )
    active = await User.objects.filter(name__startswith="A")
```
  </div>
</section>

<div class="mongoz-proof" markdown>

<span>Python 3.10–3.14</span>
<span>PyMongo Async</span>
<span>Pydantic 2</span>
<span>Typed package</span>

</div>

<div class="mongoz-grid" markdown>

<article class="mongoz-card" markdown>
### Documents with boundaries

Pydantic-backed documents validate modeled fields and serialize deliberately to BSON. Embedded
documents, references, inheritance, and native-driver escape hatches stay explicit.

[Understand documents →](concepts/documents.md)
</article>

<article class="mongoz-card" markdown>
### Queries you can compose

Managers and QuerySets use clone-on-write state, so deriving a filter, sort, projection, limit, or
session-bound query does not mutate the query you started from.

[Explore querying →](guides/querying.md)
</article>

<article class="mongoz-card" markdown>
### Index changes you can inspect

Plan index reconciliation before execution. Mongoz retains unmanaged indexes unless deletion is
explicitly authorized and treats conflicting names as a decision, not a guess.

[Plan indexes →](guides/indexes.md)
</article>

<article class="mongoz-card" markdown>
### Native where it matters

Sessions, transactions, timeouts, concerns, monitoring, and deployment topology remain PyMongo and
MongoDB contracts. Mongoz exposes the driver objects instead of hiding them.

[Run in production →](operations/index.md)
</article>

</div>

## A realistic first flow

Mongoz does no database or index I/O when a document class is imported. Create one `Registry` for
the application lifecycle, use document managers for modeled operations, and close the Registry on
shutdown. For bounded scripts, the async context manager owns cleanup.

```python
from mongoz import Document, Integer, Registry, String

registry = Registry("mongodb://localhost:27017")

class Book(Document):
    title: str = String(min_length=1)
    year: int = Integer(minimum=1450)

    class Meta:
        registry = registry
        database = "library"

async def main() -> None:
    async with registry:
        book = await Book.objects.create(title="The Left Hand of Darkness", year=1969)
        found = await Book.objects.get(id=book.id)
        await found.update(year=1969)
        await found.delete()
```

!!! info "Choose the next path"
    New users should continue with [Installation](start/installation.md) and the
    [Quickstart](start/quickstart.md). Existing applications should read the
    [modernization migration guide](migration/modernization.md) before changing dependencies or
    lifecycle code.
