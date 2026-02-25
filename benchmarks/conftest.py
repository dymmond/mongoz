import asyncio
import os
import typing

import pytest

from mongoz.core.connection.registry import Registry

database_uri = os.environ.get(
    "DATABASE_URI", "mongodb://root:mongoadmin@localhost:27017"
)
client = Registry(database_uri, event_loop=asyncio.get_running_loop)


@pytest.fixture(scope="module")
def anyio_backend():
    return ("asyncio", {"debug": False})


@pytest.fixture(scope="session")
def event_loop() -> typing.Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
