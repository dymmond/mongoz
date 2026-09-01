import asyncio
import contextvars
import threading
from collections.abc import AsyncGenerator, Generator

import pytest

from mongoz import run_sync

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
async def test_database() -> AsyncGenerator[None, None]:
    """Override shared database setup because these pure tests perform no MongoDB I/O."""
    yield


async def value(result: str = "complete") -> str:
    return result


async def test_run_sync_without_a_running_event_loop() -> None:
    assert await asyncio.to_thread(run_sync, value()) == "complete"


async def test_run_sync_preserves_runtime_error_without_retrying() -> None:
    calls = 0
    failure = RuntimeError("application failure")

    async def failing() -> None:
        nonlocal calls
        calls += 1
        raise failure

    with pytest.raises(RuntimeError) as raised:
        await asyncio.to_thread(run_sync, failing())

    assert raised.value is failure
    assert calls == 1


async def test_run_sync_preserves_other_exceptions() -> None:
    failure = LookupError("application failure")

    async def failing() -> None:
        raise failure

    with pytest.raises(LookupError) as raised:
        await asyncio.to_thread(run_sync, failing())

    assert raised.value is failure


async def test_run_sync_accepts_non_coroutine_awaitables() -> None:
    class AwaitableValue:
        def __await__(self) -> Generator[None, None, int]:
            if False:
                yield
            return 42

    assert await asyncio.to_thread(run_sync, AwaitableValue()) == 42


async def test_run_sync_reused_coroutine_raises() -> None:
    coroutine = value()

    assert await asyncio.to_thread(run_sync, coroutine) == "complete"
    with pytest.raises(RuntimeError, match="cannot reuse already awaited coroutine"):
        await asyncio.to_thread(run_sync, coroutine)


async def test_run_sync_preserves_cancellation() -> None:
    async def cancelled() -> None:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await asyncio.to_thread(run_sync, cancelled())


async def test_run_sync_uses_one_context_aware_thread_under_a_running_loop() -> None:
    marker = contextvars.ContextVar("marker", default="missing")
    marker.set("caller")
    caller_thread = threading.get_ident()
    calls = 0

    async def inspect_execution() -> tuple[int, str]:
        nonlocal calls
        calls += 1
        return threading.get_ident(), marker.get()

    worker_thread, context_value = run_sync(inspect_execution())

    assert worker_thread != caller_thread
    assert context_value == "caller"
    assert calls == 1


async def test_run_sync_preserves_runtime_error_under_a_running_loop() -> None:
    calls = 0
    failure = RuntimeError("application failure")

    async def failing() -> None:
        nonlocal calls
        calls += 1
        raise failure

    with pytest.raises(RuntimeError) as raised:
        run_sync(failing())

    assert raised.value is failure
    assert calls == 1


async def test_run_sync_rejects_loop_bound_futures_clearly() -> None:
    future = asyncio.get_running_loop().create_future()
    future.set_result("complete")

    with pytest.raises(RuntimeError, match="Future or Task bound to another event loop"):
        run_sync(future)
