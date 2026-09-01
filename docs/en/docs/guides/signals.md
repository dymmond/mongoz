---
title: Signals
description: Register Mongoz async signal receivers with deterministic ordering, fail-fast errors, cancellation propagation, and per-document isolation.
---

# Signals

Documents expose `pre_save`, `post_save`, `pre_update`, `post_update`, `pre_delete`, and
`post_delete` signals. Custom signals may be added to a document's broadcaster.

## Async-only receivers

```python
from mongoz.core.signals import post_save

@post_save(User)
async def audit_user(*, sender: type[User], instance: User) -> None:
    await audit_log.write(document_id=str(instance.id))
```

Receivers must be async callables and accept keyword arguments. Invalid or synchronous receivers
raise `SignalError` at registration rather than later during dispatch.

## Dispatch contract

Receivers run sequentially in registration order. Duplicate registration is a no-op. Dispatch is
fail-fast: the first receiver exception is preserved and later receivers do not run. Cancellation
reaches the active receiver and is not translated.

Signals keep strong references to connected receivers. `disconnect(receiver)` returns whether the
receiver was present, which makes explicit lifecycle cleanup testable.

## Ownership

Each concrete document class owns its broadcaster. Abstract documents, concrete children, and
siblings do not accidentally share receiver lists or custom signal mutations.

## Transaction and retry implications

Receivers execute in the operation's task; Mongoz does not create background tasks. A `post_*`
receiver can fail after the database write succeeded. Do not assume a raised receiver exception
means the write can safely be repeated. Use an outbox or another durable application design when a
side effect must be coordinated with a transaction.
