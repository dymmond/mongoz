---
title: Introduction
description: Learn where Mongoz fits, which responsibilities it owns, and when to use native PyMongo Async directly.
---

# Introduction

Mongoz is an asynchronous object-document mapper for MongoDB. It gives Python applications typed
documents, Pydantic validation, composable queries, deliberate persistence semantics, and
inspectable index reconciliation while retaining native PyMongo Async access.

## What Mongoz owns

Mongoz owns the mapping between declared Python document fields and MongoDB BSON documents. It also
owns its public query vocabulary, clone-on-write query state, modeled create/update/save behavior,
document signals, and index planning policy.

PyMongo and MongoDB continue to own connections, topology discovery, pooling, sessions,
transactions, read and write concerns, retries, timeouts, BSON server limits, and native errors.
Mongoz exposes `registry.driver`, `database.driver`, and `collection.driver` when that lower-level
control is the correct tool.

## A deliberate async lifecycle

Mongoz uses PyMongo's native asynchronous driver, not Motor. Constructing a `Registry` creates one
`AsyncMongoClient`, but imports do not contact MongoDB and document declaration does not create
indexes. The first operation binds the client to the active event loop. Close the Registry from
that lifecycle; a closed Registry is final.

## When Mongoz is a good fit

Use Mongoz when your application benefits from:

- Pydantic-backed document validation and serialization;
- type-aware document fields and a `py.typed` package;
- reusable modeled queries without shared mutable query state;
- explicit index inspection and reconciliation;
- async sessions, transactions, aggregation, and bulk-write access; and
- a direct route to native PyMongo behavior when the ODM abstraction is not enough.

Use PyMongo directly for workloads dominated by dynamic pipelines, raw collections without a
stable model, or driver features that would be obscured by an ODM layer. Mixing modeled and native
operations is supported when ownership remains explicit.

## Documentation map

The [Quickstart](quickstart.md) builds a complete lifecycle. [Concepts](../concepts/index.md) explain
the mental model, [Tutorials](../tutorials/index.md) assemble larger flows, and
[Guides](../guides/index.md) answer focused implementation questions. Existing applications should
start with [Migration](../migration/index.md); operators should use the
[production checklist](../operations/index.md).
