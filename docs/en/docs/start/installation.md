---
title: Installation
description: Install Mongoz, verify supported Python and dependency ranges, and prepare a MongoDB deployment for development.
---

# Installation

Mongoz supports CPython 3.10 through 3.14. Install the package from PyPI:

```console
python -m pip install mongoz
```

The runtime dependency range is intentionally bounded:

| Dependency | Supported range | Owner |
| --- | --- | --- |
| Python | 3.10–3.14 | Mongoz package and CI matrix |
| PyMongo | `>=4.13,<5.0` | Native async driver, BSON, sessions, transactions |
| Pydantic | `>=2.10,<3.0` | Model validation and serialization |
| Pydantic Settings | `>=2.9,<3.0` | Lazy Mongoz settings |

See [Compatibility](../reference/compatibility.md) for the distinction between tested, supported,
and topology-specific behavior.

## Confirm the installation

```python
import mongoz

print(mongoz.__version__)
```

Mongoz ships `mongoz/py.typed`, so compatible type checkers consume its public annotations without
a separate stubs package. This repository uses `ty` as its canonical checker; applications may use
another PEP 561-compatible checker.

## MongoDB for local development

You need a reachable MongoDB deployment for database operations. A standalone server supports
ordinary CRUD, indexes, aggregation, and bulk writes. Multi-document transactions require a
replica set or sharded cluster.

Keep credentials outside source code. These pages use a credential-free localhost URI only for
development examples:

```python
from mongoz import Registry

registry = Registry("mongodb://localhost:27017")
```

Configure timeouts, TLS, authentication, retry behavior, and concerns through the PyMongo URI or
native driver options described in [PyMongo configuration and resilience](../guides/pymongo-configuration.md).

## Upgrade warning

If an existing application imports Motor types or assumes Registry clients can be reopened, do not
upgrade dependencies in isolation. Follow the [modernization migration guide](../migration/modernization.md).
