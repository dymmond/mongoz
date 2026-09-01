from __future__ import annotations

import asyncio
import contextvars
from concurrent import futures
from typing import Awaitable, TypeVar

T = TypeVar("T")


def run_sync(async_function: Awaitable[T]) -> T:
    """Run one awaitable to completion from synchronous code.

    When called while an event loop is already running in the current thread,
    the awaitable runs once in a worker thread with the caller's context
    variables. Exceptions raised by the awaitable are propagated unchanged.
    """

    if isinstance(async_function, asyncio.Future):
        raise RuntimeError(
            "run_sync cannot consume an asyncio Future or Task bound to another event loop"
        )

    async def consume() -> T:
        return await async_function

    def runner() -> T:
        return asyncio.run(consume())

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return runner()

    context = contextvars.copy_context()

    def context_runner() -> T:
        return context.run(runner)

    with futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(context_runner)
        return future.result()
