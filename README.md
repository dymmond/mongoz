# Mongoz

<p align="center">
  <a href="https://mongoz.dymmond.com"><img src="https://res.cloudinary.com/tarsild/image/upload/v1695724284/packages/mongoz/nwtcudxmncgoyw4em0th.png" alt="Mongoz"></a>
</p>

<p align="center"><strong>Typed asynchronous MongoDB documents and queries for Python.</strong></p>

<p align="center">
  <a href="https://github.com/dymmond/mongoz/actions/workflows/test-suite.yml"><img src="https://github.com/dymmond/mongoz/actions/workflows/test-suite.yml/badge.svg?event=push&branch=main" alt="Test Suite"></a>
  <a href="https://pypi.org/project/mongoz"><img src="https://img.shields.io/pypi/v/mongoz?color=%234b4fd8&label=pypi%20package" alt="Package version"></a>
  <a href="https://pypi.org/project/mongoz"><img src="https://img.shields.io/pypi/pyversions/mongoz.svg?color=%23087f9d" alt="Supported Python versions"></a>
</p>

Mongoz is an asynchronous object-document mapper for MongoDB, built on native
[PyMongo Async](https://pymongo.readthedocs.io/en/stable/async-tutorial.html) and
[Pydantic](https://docs.pydantic.dev/). It combines typed documents, composable clone-on-write
queries, deliberate persistence semantics, inspectable index reconciliation, sessions,
transactions, aggregation, bulk writes, and direct native-driver escape hatches.

- **Documentation:** [mongoz.dymmond.com](https://mongoz.dymmond.com)
- **Source:** [github.com/dymmond/mongoz](https://github.com/dymmond/mongoz)
- **Migration:** [modernization guide](https://mongoz.dymmond.com/migration/modernization/)

## Installation

```console
python -m pip install mongoz
```

Mongoz supports Python 3.10–3.14, PyMongo `>=4.13,<5.0`, and Pydantic 2. The package ships
`py.typed` for PEP 561 consumers.

## Quickstart

```python
from mongoz import Boolean, Document, Registry, String

registry = Registry("mongodb://localhost:27017")


class User(Document):
    name: str = String(min_length=1, max_length=80)
    email: str = String(unique=True)
    active: bool = Boolean(default=True)

    class Meta:
        registry = registry
        database = "app"


async def main() -> None:
    async with registry:
        user = await User.objects.create(name="Ada", email="ada@example.com")

        found = await User.objects.get(id=user.id)
        active_users = await User.objects.filter(active=True).sort("name")

        await found.update(name="Ada Lovelace")
        await found.delete()

        assert active_users[0].email == "ada@example.com"
```

A Registry owns one PyMongo `AsyncMongoClient`. Reuse it for the application lifecycle and close it
during shutdown; a closed Registry is final. Document declaration performs no database or index I/O.

## Why Mongoz

- Pydantic-backed `Document` and `EmbeddedDocument` models
- familiar Manager filters and explicit `Q`/field expressions
- immutable query derivation for safe reuse
- atomic patch updates and explicit full-model save behavior
- index planning before reviewed reconciliation
- PyMongo Async sessions, transactions, aggregation, and bulk writes
- deterministic async-only document signals
- typed native client, database, collection, cursor, and session boundaries
- security guidance for raw queries, regex, credentials, and destructive indexes

Mongoz does not replace PyMongo's ownership of topology, pooling, timeouts, retries, read/write
concerns, native errors, or transaction lifecycle. Use `registry.driver`, `database.driver`, and
`collection.driver` when the driver is the right abstraction.

## Documentation

New users should begin with the [Quickstart](https://mongoz.dymmond.com/start/quickstart/). Existing
applications should review the [migration guide](https://mongoz.dymmond.com/migration/modernization/).
Production deployments should use the
[operations checklist](https://mongoz.dymmond.com/operations/) and
[security guide](https://mongoz.dymmond.com/guides/security/).

## Contributing and security

The [contributor guide](https://mongoz.dymmond.com/project/contributing/) documents the Zensical
documentation workflow, quality gates, real MongoDB topologies, typing checks, and package proof.

Report suspected vulnerabilities privately through the repository Security tab according to
[`SECURITY.md`](SECURITY.md), not through a public issue.
