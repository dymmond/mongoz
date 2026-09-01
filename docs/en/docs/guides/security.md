---
title: Security
description: Protect Mongoz connection secrets, raw MongoDB query boundaries, tenant predicates, regex execution, index deletion, and monitoring data.
---

# Security

Mongoz validates modeled data; it is not an authorization layer or a MongoDB query firewall.

## Secrets and transport

Load the MongoDB URI from a deployment secret source. Do not put credentials in source, command
arguments, logs, exceptions, trace attributes, or metric labels. `registry.url` may contain the
complete configured URI and must not be logged. Configure TLS and certificate verification using
supported PyMongo options and deployment policy.

## Trusted query surfaces

Raw dictionaries, `Manager.raw()`, dictionary `query()` arguments, raw `Expression` objects,
aggregation pipelines, bulk-write requests, raw regex patterns, `$where`, and native driver access
are trusted developer interfaces. Never pass decoded request mappings through them.

Build allowlisted operations in application code. Apply authorization and tenant predicates at the
same canonical boundary on every read and write; database or collection selection must also be
validated rather than accepted from request text.

## Modeled fields are not permissions

`read_only` metadata communicates model intent. It does not prevent a raw query or native write.
Use dedicated request schemas and explicit allowlists for server-owned fields. Bound request depth,
size, array lengths, and search complexity before model construction.

## Regex and JavaScript

Literal string helpers escape regex metacharacters. `Q.pattern()` does not. Bound untrusted search
input even for literal helpers. Treat `$where` as legacy trusted-only JavaScript and migrate to
ordinary operators or `$expr`.

## Destructive index policy

Unmanaged indexes are retained by default. Review plans before using `force_drop=True`,
`drop_unmanaged=True`, or `drop_indexes(force=True)`. Index ownership is a deployment and migration
decision, not something to infer from current model metadata alone.

## Monitoring and reports

PyMongo command monitoring can contain collection names, query values, and update documents. Apply
the same data classification and redaction policy used for application logs. Report suspected
Mongoz vulnerabilities privately through the repository Security tab, following `SECURITY.md`.
