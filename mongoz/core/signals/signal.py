from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Tuple, Type, Union

from mongoz.exceptions import SignalError
from mongoz.utils.inspect import func_accepts_kwargs

if TYPE_CHECKING:
    from mongoz import Document


Receiver = Callable[..., Awaitable[object]]


def make_id(target: Any) -> Union[int, Tuple[int, int]]:
    """
    Creates an id for a function.
    """
    if hasattr(target, "__func__"):
        return (id(target.__self__), id(target.__func__))
    return id(target)


class Signal:
    """
    Base class for all Mongoz signals.
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Creates a new signal.
        """
        self.receivers: Dict[Union[int, Tuple[int, int]], Receiver] = {}

    def connect(self, receiver: Receiver) -> None:
        """
        Connects a given receiver to the the signal.
        """
        if not callable(receiver):
            raise SignalError("Signal receivers must be callable.")

        receiver_call = type(receiver).__call__
        if not (
            inspect.iscoroutinefunction(receiver) or inspect.iscoroutinefunction(receiver_call)
        ):
            raise SignalError("Signal receivers must be async callables.")

        if not func_accepts_kwargs(receiver):
            raise SignalError("Signal receivers must accept keyword arguments (**kwargs).")

        key = make_id(receiver)
        if key not in self.receivers:
            self.receivers[key] = receiver

    def disconnect(self, receiver: Receiver) -> bool:
        """
        Removes the receiver from the signal.
        """
        key = make_id(receiver)
        func: Union[Receiver, None] = self.receivers.pop(key, None)
        return True if func is not None else False

    async def send(self, sender: Type["Document"], **kwargs: Any) -> None:
        """
        Sends the notification to all the receivers.
        """
        for receiver in tuple(self.receivers.values()):
            await receiver(sender=sender, **kwargs)


class Broadcaster(dict):
    def __getattr__(self, item: str) -> Signal:
        return self.setdefault(item, Signal())

    def __setattr__(self, __name: str, __value: Signal) -> None:
        if not isinstance(__value, Signal):
            raise SignalError(f"{__value!r} is not a valid Signal.")
        self[__name] = __value
