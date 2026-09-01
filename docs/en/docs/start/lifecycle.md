---
title: Registry lifecycle
description: Own one Mongoz Registry per application lifecycle, bind it to one event loop, and close it deterministically.
---

# Registry lifecycle

A `Registry` constructs and owns exactly one PyMongo `AsyncMongoClient`. Databases, collections,
documents, managers, and QuerySets derived from it reuse that client and its connection pools.

## Application lifetime

Create the Registry with application configuration, then close it during shutdown:

```python
{!> docs_src/examples/lifecycle.py !}
```

`close()` is async and idempotent. Closing is final: the Registry does not manufacture a replacement
client and cannot be reopened. A database or collection wrapper obtained earlier is also invalid
after its Registry is closed.

## Bounded work

Use the async context manager for scripts, jobs, and tests whose ownership fits a lexical scope:

```python
async with Registry("mongodb://localhost:27017") as registry:
    database = registry.get_database("analytics")
    await database.driver.command("ping")
```

If the body and cleanup both fail, Mongoz preserves the body failure and chains the cleanup failure
as its cause. Cancellation is not translated.

## Event-loop ownership

The native async client becomes bound to the loop that performs its first database operation. Do
not share a Registry across event loops. Test suites that create a fresh loop per test should either
use one loop-scoped Registry or construct and close a Registry inside each loop-owned fixture.

!!! warning "No import-time I/O"
    Importing document modules must not ping MongoDB or reconcile indexes. Call
    `registry.document_checks()` from an explicit startup hook when automatic index checks are part
    of your deployment policy.

Read [Registry, database, and collection](../concepts/registry-boundaries.md) for the wrapper model
and [Production setup](../tutorials/production.md) for an application lifecycle example.
