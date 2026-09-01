---
title: Testing applications using Mongoz
description: Test Mongoz applications against real MongoDB with loop-owned Registry fixtures, isolated databases, index proof, and replica-set transaction coverage.
---

# Testing applications using Mongoz

Use real MongoDB when behavior depends on server semantics. Mocks can prove application branching,
but not BSON encoding, index conflict behavior, sessions, transactions, server selection, or native
errors.

## Loop-owned fixture

```python
import pytest
from mongoz import Registry

@pytest.fixture
async def registry():
    value = Registry("mongodb://localhost:27017")
    try:
        yield value
    finally:
        await value.close()
```

Make the fixture scope compatible with the test runner's event-loop scope. A session-scoped Registry
cannot be used safely if each test receives an unrelated loop.

## Isolate state

Use a dedicated database name per worker or test group. Drop that database during teardown only
when the URI and database target are test-owned and explicit. Create indexes required by the test;
do not rely on import-time generation.

## Proof by behavior

- CRUD tests should read the stored document back.
- Index tests should inspect `list_indexes()` and exercise uniqueness.
- Aggregation and bulk tests should assert native result shapes and stored effects.
- Cancellation tests should prove cursor cleanup and original failure propagation.
- Transaction tests must run against a replica set and verify commit and abort state.
- Typing fixtures should run against an installed wheel when package metadata is part of the claim.

The Mongoz repository provides deterministic standalone and replica-set Compose topologies. See
[Contributing](../project/contributing.md) for the canonical commands.
