import asyncio
import typing

import pytest

from mongoz.core.connection.registry import Registry
from tests.settings import TEST_DATABASE_URL

database_uri = TEST_DATABASE_URL
client = Registry(database_uri, event_loop=asyncio.get_running_loop)


@pytest.fixture(scope="module")
def anyio_backend():
    return ("asyncio", {"debug": False})


@pytest.fixture(scope="session")
def event_loop() -> typing.Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def test_database() -> typing.AsyncGenerator:
    await client.drop_database("test_db")
    yield
    await client.drop_database("test_db")
