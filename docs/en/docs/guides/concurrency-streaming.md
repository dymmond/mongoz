---
title: Concurrency and streaming
description: Stream large Mongoz queries, close cursors on early exit, propagate cancellation, and avoid unsafe session or Registry concurrency.
---

# Concurrency and streaming

## Stream large reads

`all()`, awaited Managers, `values()`, `values_list()`, `where()`, high-level aggregation, and
high-level update methods materialize results. Use async iteration for large document reads:

```python
async for user in User.objects.filter(active=True).sort("id").limit(10_000):
    await process(user)
```

Streaming preserves filter, sort, skip, limit, projection, relation lookup, and session state.
PyMongo owns cursor batching and network backpressure.

## Early exit

Mongoz closes its cursor on normal completion, failure, and cancellation. If application code keeps
the iterator after breaking, close it explicitly:

```python
iterator = User.objects.filter(active=True).__aiter__()
try:
    async for user in iterator:
        await process(user)
        if should_stop(user):
            break
finally:
    await iterator.aclose()
```

Use the native cursor when a strict `batch_size()` or another unmodeled cursor option is required.

## Concurrency boundaries

Immutable query derivations can be evaluated independently, but one PyMongo session must not be used
concurrently. Do not share a session across tasks or `asyncio.gather()` calls. A Registry may serve
concurrent work on its owning event loop, but not work from another loop.

Mongoz preserves `asyncio.CancelledError`. Application cleanup belongs in `finally`; catch broad
exceptions only when cancellation is re-raised unchanged.

## Synchronous boundaries

`run_sync(awaitable)` executes the awaitable exactly once. Without a running loop it uses
`asyncio.run()`. With a loop already running in the current thread, it copies context variables and
blocks while a worker thread runs the awaitable. It is a bridge for synchronous callers, not a
non-blocking API for async request handlers.
