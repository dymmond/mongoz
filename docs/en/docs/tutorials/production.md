---
title: Production setup
description: Assemble Mongoz Registry ownership, secrets, startup checks, shutdown cleanup, and native PyMongo configuration for production.
---

# Production setup

A production integration has one configuration owner, one long-lived Registry per application
lifecycle, optional explicit startup index checks, and deterministic shutdown.

## Configuration boundary

```python
import os
from mongoz import Registry

def create_registry() -> Registry:
    uri = os.environ["MONGODB_URI"]
    return Registry(uri)
```

Do not log the URI. `registry.url` intentionally retains it for compatibility and may contain
credentials. Use a deployment secret source and configure TLS, authentication, timeouts, retries,
and concerns through supported PyMongo URI options.

## Lifecycle boundary

```python
registry = create_registry()

async def start_database() -> None:
    await registry.driver.admin.command("ping")
    await registry.document_checks()

async def stop_database() -> None:
    await registry.close()
```

Call these functions from the framework's startup and shutdown hooks. Do not create a client per
request: that discards pooling and repeats topology discovery and authentication work.

`document_checks()` is optional deployment policy. It calls `check_indexes()` for every concrete
document registered with this Registry. For sensitive changes, inspect `plan_indexes()` during a
migration and execute a reviewed policy separately.

## Before traffic

- Verify server selection and authentication with `ping`.
- Confirm the deployment topology supports required transactions.
- Review index plans and unique-index data constraints.
- Set bounded selection, connect, socket, queue, and operation timeouts.
- Confirm read/write concern and retry policy match durability requirements.
- Install monitoring with query-value redaction.

Continue with the [production checklist](../operations/index.md),
[security guide](../guides/security.md), and
[PyMongo configuration](../guides/pymongo-configuration.md).
