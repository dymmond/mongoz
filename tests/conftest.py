import asyncio
import os
import typing

import pytest

from mongoz.core.connection.registry import Registry

database_uri = os.environ.get("DATABASE_URI", "mongodb://root:mongoadmin@localhost:27017")
client = Registry(database_uri, event_loop=asyncio.get_running_loop)


@pytest.fixture(scope="session")
def event_loop() -> typing.Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
async def test_database() -> typing.AsyncGenerator:
    await client.drop_database("test_db")
    yield
    await client.drop_database("test_db")
