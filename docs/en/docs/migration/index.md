---
title: Upgrade overview
description: Plan a Mongoz upgrade by inventorying driver types, Registry lifecycle, query reuse, persistence, indexes, sessions, signals, and raw query boundaries.
---

# Upgrade overview

Modern Mongoz corrects several contracts that older applications may have relied on accidentally.
Treat the upgrade as an application lifecycle and behavior migration, not only a dependency bump.

## Before changing packages

Inventory:

- Motor imports, annotations, mocks, and event-loop assumptions;
- where each Registry is created, first used, and closed;
- startup code that expects automatic index creation;
- reused Manager or QuerySet chains;
- code that treats `.none()` as a synchronous mutator;
- instance `update()` and `save()` expectations;
- raw query, regex, aggregation, and bulk input sources;
- sessions that are implicit, omitted, or used concurrently;
- signal receivers that are synchronous or depend on unordered execution;
- catches for old/internal exception types; and
- mypy-only tooling or suppressions that hide public typing defects.

Add focused regression tests around each discovered dependency. Then follow the
[modernization migration guide](modernization.md) in order.

## Behavior classification

Some changes are API migrations, such as Motor → PyMongo Async types. Others are correctness fixes,
such as clone-on-write queries, literal regex helpers, deterministic signals, or missing-write
errors. A correctness fix can still change observable behavior. Update callers deliberately rather
than labeling every change backward-compatible.

Historical release notes remain historical. This guide describes the current upgrade boundary and
links to current contracts instead of rewriting old releases as if the modern architecture always
existed.
