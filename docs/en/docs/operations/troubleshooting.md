---
title: Troubleshooting
description: Diagnose common Mongoz lifecycle, server selection, transaction, query, index, write, memory, warning, and documentation build failures.
---

# Troubleshooting

## Registry is closed

A closed Registry is final. Find the lifecycle owner that closed it early and create a new Registry
for the next application lifecycle. Do not mutate private client state or expect wrappers to reopen.

## Event-loop errors

The Registry was likely first used on one event loop and later shared with another. Align fixture
scope with loop scope and avoid constructing one module-global Registry for tests that create a new
loop per case.

## Server selection or timeout failures

Check the full native PyMongo error and its cause. Verify DNS, URI, authentication, TLS, topology,
and timeout budgets. Mongoz does not replace these errors. Do not log the raw URI while diagnosing.

## Transactions rejected

Confirm the deployment is a replica set or sharded cluster and that every operation receives the
same session sequentially. Standalone MongoDB cannot run multi-document transactions.

## `OperatorInvalid`

Check the lookup suffix and operand shape. Unknown operators fail eagerly; `in` and `not_in` require
a list or tuple. Use the [operator reference](../reference/querying.md).

## `DocumentNotFound` during save/update/delete

The instance identifier no longer matches a persisted document. Treat it as an optimistic-staleness or
application lifecycle event. Reload only when that recovery is correct; do not hide the missing
write.

## Index conflict

Inspect `plan_indexes()` output. A same-name different specification needs explicit recreation; an
equivalent index under another name requires a human ownership decision. Do not enable broad drop
flags merely to make startup pass.

## Memory grows during queries

Replace `all()`, `values()`, `values_list()`, `where()`, or high-level aggregation with streaming or
a bounded native cursor where possible. High-level bulk updates return hydrated documents; use a
native bounded write result when callers do not need those documents.

## Documentation build fails

Run `hatch run docs:clean` followed by `hatch run docs:validate`. The gate reports include cycles or
missing targets, Python fence syntax, compatibility-route gaps, broken links/anchors, and strict
Zensical warnings.
