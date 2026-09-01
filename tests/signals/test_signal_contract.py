import asyncio
import gc
import weakref
from collections.abc import AsyncGenerator

import pytest

import mongoz
from mongoz import Document
from mongoz.core.signals import Broadcaster, Signal
from mongoz.exceptions import SignalError
from tests.conftest import client

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
async def test_database() -> AsyncGenerator[None, None]:
    """Keep pure signal contract tests independent from MongoDB availability."""
    yield


async def test_sync_receiver_is_rejected_at_registration() -> None:
    signal = Signal()

    def receiver(sender: type[Document], **kwargs: object) -> None:
        del sender, kwargs

    with pytest.raises(SignalError, match="async callables"):
        signal.connect(receiver)


async def test_receivers_run_sequentially_in_registration_order() -> None:
    signal = Signal()
    events: list[str] = []

    async def first(sender: type[Document], **kwargs: object) -> None:
        del sender, kwargs
        events.append("first:start")
        await asyncio.sleep(0)
        events.append("first:end")

    async def second(sender: type[Document], **kwargs: object) -> None:
        del sender, kwargs
        events.append("second")

    signal.connect(first)
    signal.connect(second)

    result = await signal.send(sender=Document)

    assert result is None
    assert events == ["first:start", "first:end", "second"]


async def test_duplicate_registration_is_a_noop_and_disconnect_reports_presence() -> None:
    signal = Signal()
    calls = 0

    async def receiver(sender: type[Document], **kwargs: object) -> None:
        nonlocal calls
        del sender, kwargs
        calls += 1

    signal.connect(receiver)
    signal.connect(receiver)

    await signal.send(sender=Document)

    assert calls == 1
    assert signal.disconnect(receiver) is True
    assert signal.disconnect(receiver) is False


async def test_receiver_failure_is_preserved_and_stops_later_receivers() -> None:
    signal = Signal()
    calls: list[str] = []
    failure = RuntimeError("receiver failed")

    async def failing(sender: type[Document], **kwargs: object) -> None:
        del sender, kwargs
        calls.append("failing")
        raise failure

    async def later(sender: type[Document], **kwargs: object) -> None:
        del sender, kwargs
        calls.append("later")

    signal.connect(failing)
    signal.connect(later)

    with pytest.raises(RuntimeError) as raised:
        await signal.send(sender=Document)

    assert raised.value is failure
    assert calls == ["failing"]


async def test_cancellation_reaches_active_receiver_and_stops_dispatch() -> None:
    signal = Signal()
    started = asyncio.Event()
    cancelled = asyncio.Event()
    later_called = False

    async def blocking(sender: type[Document], **kwargs: object) -> None:
        del sender, kwargs
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    async def later(sender: type[Document], **kwargs: object) -> None:
        nonlocal later_called
        del sender, kwargs
        later_called = True

    signal.connect(blocking)
    signal.connect(later)
    dispatch = asyncio.create_task(signal.send(sender=Document))
    await started.wait()

    dispatch.cancel()

    with pytest.raises(asyncio.CancelledError):
        await dispatch
    assert cancelled.is_set()
    assert later_called is False


async def test_signal_keeps_a_strong_reference_to_connected_receiver() -> None:
    signal = Signal()

    class Receiver:
        async def __call__(self, sender: type[Document], **kwargs: object) -> None:
            del sender, kwargs

    receiver = Receiver()
    reference = weakref.ref(receiver)
    signal.connect(receiver)
    del receiver
    gc.collect()

    assert reference() is not None


async def test_document_signal_namespaces_are_owned_per_model() -> None:
    class AbstractRecord(Document):
        name: str = mongoz.String()

        class Meta:
            abstract = True
            registry = client
            database = "test_db"

    class FirstRecord(AbstractRecord):
        pass

    class SecondRecord(AbstractRecord):
        pass

    async def receiver(sender: type[Document], **kwargs: object) -> None:
        del sender, kwargs

    AbstractRecord.signals.pre_save.connect(receiver)
    FirstRecord.signals.pre_save.connect(receiver)
    FirstRecord.signals.custom.connect(receiver)

    assert AbstractRecord.signals is not FirstRecord.signals
    assert FirstRecord.signals is not SecondRecord.signals
    assert receiver in AbstractRecord.signals.pre_save.receivers.values()
    assert receiver in FirstRecord.signals.pre_save.receivers.values()
    assert receiver not in SecondRecord.signals.pre_save.receivers.values()
    assert "custom" not in AbstractRecord.signals
    assert "custom" not in SecondRecord.signals


async def test_broadcaster_rejects_non_signal_values_with_context() -> None:
    broadcaster = Broadcaster()

    with pytest.raises(SignalError, match=r"'invalid'.*not a valid Signal"):
        broadcaster.custom = "invalid"
