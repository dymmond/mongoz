# Production performance, security, and resilience

This guide defines the operational boundary between Mongoz, PyMongo/MongoDB, and the application.
It describes contracts rather than performance promises: topology, network, dataset, indexes, and
application behavior usually dominate end-to-end latency.

## Client ownership and secrets

Create one `Registry` per application lifecycle and reuse it. It owns one PyMongo
`AsyncMongoClient`; constructing clients per request discards connection pooling and adds avoidable
server discovery and authentication work. Close the Registry from the same event loop during
shutdown, or use its async context manager for bounded work.

Load MongoDB URIs from a deployment secret source. Do not place credentials in source, command-line
arguments, logs, exception messages, tracing attributes, or monitoring labels. Default Registry and
PyMongo client representations do not expose URI credentials, but `registry.url` intentionally
retains the configured URI for compatibility and must not be logged.

## Timeouts, retries, and concerns

Mongoz passes the complete URI to PyMongo and does not create a competing timeout or retry layer.
Configure `serverSelectionTimeoutMS`, `connectTimeoutMS`, `socketTimeoutMS`,
`waitQueueTimeoutMS`, and `timeoutMS` with native PyMongo URI options where appropriate:

```python
registry = Registry(
    "mongodb://db.example/app?serverSelectionTimeoutMS=5000&connectTimeoutMS=3000"
    "&socketTimeoutMS=10000&waitQueueTimeoutMS=2000&timeoutMS=15000"
)
```

For a narrower operation budget, use PyMongo's client-side timeout context:

```python
import pymongo

with pymongo.timeout(2.5):
    user = await User.objects.get(email="user@example.com")
```

Timeouts, server-selection failures, duplicate keys, bulk partial failures, write-concern failures,
and transaction failures retain their native PyMongo exception types. Catch only errors for which
the application has a deliberate recovery policy.

PyMongo also owns retryable reads/writes, read preference, read concern, and write concern. Mongoz
does not override driver defaults. Configure client-wide behavior in the URI and use
`collection.driver.with_options(...)` for an operation-specific native collection. Retrying an
application transaction or a multi-step workflow is an application responsibility because only the
application knows whether its side effects are idempotent.

## Cancellation and failure recovery

Mongoz does not translate `asyncio.CancelledError`. Cursor-backed operations close their cursor on
normal completion, failure, cancellation, and explicit iterator close. Registry context cleanup
preserves the body exception if cleanup also fails, chaining the cleanup error as its cause.

Do not catch cancellation broadly. Use `finally` for application-owned cleanup and re-raise the
original cancellation. A failed database operation does not automatically poison an open Registry;
subsequent operations may reuse it when PyMongo's topology state permits. A successfully closed
Registry is final and must be replaced.

Sessions and transactions belong to PyMongo. Use them sequentially, propagate the same session to
every operation, and let the transaction context abort on exceptions. After an abort, the Registry
and session remain governed by PyMongo's lifecycle contract; start a new transaction rather than
reusing an ended transaction.

Signal receivers are awaited sequentially and do not create background tasks. Receiver exceptions
and cancellation are preserved. A receiver can fail after its associated database write has already
completed, so do not blindly repeat the write when recovering from a signal error.

## Large results and memory

`all()`, `values()`, `values_list()`, `where()`, high-level aggregation, and list-returning update
operations materialize results. Their memory use scales with result cardinality. Use async iteration
for large reads:

```python
async for user in User.objects.filter(is_active=True).sort("email").limit(10_000):
    await process(user)
```

Streaming preserves filters, ordering, projection, skip, limit, lookups, and sessions. If code keeps
the iterator after breaking early, close it explicitly:

```python
iterator = User.objects.filter(is_active=True).__aiter__()
try:
    async for user in iterator:
        await process(user)
        if should_stop(user):
            break
finally:
    await iterator.aclose()
```

PyMongo controls cursor batches and backpressure. When a strict batch policy is required, use the
native escape hatch, for example `User.get_collection().driver.find(...).batch_size(100)`. For broad
updates where returned models are unnecessary, prefer native `update_many()` or `bulk_write()` so
the driver can return a bounded result instead of a list of hydrated documents.

## Raw query and document boundaries

Normal modeled persistence writes declared fields only. Undeclared values can still be present on a
hydrated model for schemaless MongoDB compatibility, but are not silently persisted by modeled
create/save paths. Field metadata such as `read_only` is not request authorization; applications
must use input schemas and explicit allowlists for server-owned fields.

Raw filter dictionaries, dictionary arguments to `query()`, raw `Expression` objects, aggregation
pipelines, bulk writes, regex patterns, and native driver access are trusted developer interfaces.
Never forward decoded request mappings into them. Independently apply authorization and tenant
predicates in application-owned code.

The string helpers `contains`, `icontains`, `startswith`, and `endswith` escape metacharacters and
have literal semantics. `Q.pattern()` is the explicit raw-regex interface. Bound user search length
and complexity even when a literal helper is used.

`where()` is a legacy trusted-only escape hatch for MongoDB `$where` JavaScript. MongoDB 8.0
deprecates server-side JavaScript, and `$where` cannot use indexes. Prefer ordinary operators or
`$expr`; never interpolate request values into JavaScript.

PyMongo and MongoDB own BSON type validation, maximum document size, key restrictions, and server
limits. Mongoz preserves those failures. Applications should bound request size/depth before model
construction; do not rely on BSON encoding as an input-limiting mechanism.

## Observability

Use PyMongo command monitoring and deployment telemetry rather than a parallel Mongoz tracing
system. Monitoring payloads can contain query values and collection names: apply the same data
classification and redaction policy used for application logs, and never attach raw connection
URIs. Keep debug instrumentation disabled during performance measurements.

## Performance evidence

The maintained CodSpeed microbenchmarks use Python 3.13, fixed workloads, 20 warmup rounds, and 100
measured rounds. They protect model construction, dump/BSON serialization, single and bulk
hydration, persistence/update payloads, expression compilation, and immutable query cloning.
CodSpeed comparisons are regression-oriented; results are not cross-ODM marketing claims. A stable
median regression above 10% that reproduces in two canonical runs is the investigation budget, not
an automatic correctness failure. Hosted pass/fail enforcement is owned by the CodSpeed project
setting so repository code does not manufacture a second threshold.

`benchmarks/database.py` is an informational standalone MongoDB benchmark. It reports raw PyMongo
and Mongoz end-to-end groups separately with a fixed 1,000-document dataset, five warmups, nine
repeats, medians, ranges, and relative standard deviation. Run it with the pinned development
topology:

```shell
hatch run mongodb-standalone-up
hatch run matrix.py3.13:python benchmarks/database.py
hatch run mongodb-standalone-down
```

Treat pure-Python CodSpeed changes as regression-gated evidence. Database results are informational
during development; both sets become release evidence when recorded for a release candidate. Do not
infer a Mongoz optimization from a noisy end-to-end number without a separate Python-side profile.

## Runtime dependencies

Mongoz directly declares Pydantic because its model APIs are used at runtime, Pydantic Settings for
the settings owner, and PyMongo for the async driver. Pydantic/Pydantic Settings are constrained to
the supported 2.x major line; PyMongo is constrained to 4.x because 4.13 is the first supported
native async driver release. The package proof installs the lower bounds together. `orjson` is not a
runtime dependency: Mongoz has no JSON hot path that uses it, and Pydantic owns JSON serialization.
