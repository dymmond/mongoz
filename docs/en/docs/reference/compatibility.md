---
title: Compatibility
description: See Mongoz tested and supported Python, PyMongo, Pydantic, MongoDB topology, typing, and warning contracts without overstating unverified versions.
---

# Compatibility

The table distinguishes repository proof from package support. “Expected” means upstream contracts
make the combination plausible, but this repository does not claim direct evidence for every
version or deployment.

| Surface | Tested | Supported | Expected but unverified |
| --- | --- | --- | --- |
| CPython | 3.10, 3.11, 3.12, 3.13, 3.14 in hosted matrix | 3.10–3.14 | Alternative Python implementations |
| PyMongo | 4.17.0 in test environment; lower-bound wheel proof | `>=4.13,<5.0` | Future 4.x behavior not yet exercised by CI |
| Pydantic | 2.13.5 in test environment; lower-bound wheel proof | `>=2.10,<3.0` | Future 2.x behavior not yet exercised by CI |
| Pydantic Settings | 2.15.0 in test environment; lower-bound wheel proof | `>=2.9,<3.0` | Future 2.x behavior not yet exercised by CI |
| MongoDB standalone | 8.0.29 pinned image | CRUD, indexes, aggregation, bulk operations supported by compatible PyMongo/MongoDB | Other server versions within PyMongo's compatibility policy |
| MongoDB replica set | 8.0.29 pinned single-node replica set | Sessions and transactions on compatible deployments | Sharded-cluster transaction behavior not directly exercised here |
| Static typing | `ty` positive and negative fixtures; installed-wheel checks | PEP 561 consumers through `py.typed` | Exact inference parity in every third-party checker |
| Warnings | Supported test use has a zero-`UserWarning` ratchet | No warning is required for documented normal usage | Third-party deployment warnings |

Mongoz does not publish a broader MongoDB server-version matrix than its direct evidence. PyMongo's
own compatibility policy and MongoDB feature availability still apply.

Motor is not supported by the modern runtime. Public driver annotations use PyMongo Async types.
