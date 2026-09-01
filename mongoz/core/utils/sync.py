from __future__ import annotations

import asyncio
from concurrent import futures
from typing import Any, Coroutine, TypeVar

T = TypeVar("T")


def run_sync(async_function: Coroutine[Any, Any, T]) -> T:
    """
    Runs the queries in sync mode
    """

    def runner() -> T:
        return asyncio.run(async_function)

    try:
        return runner()
    except RuntimeError:
        with futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(runner)
            return future.result()
