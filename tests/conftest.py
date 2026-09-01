import typing

import pytest

from mongoz.core.connection.registry import Registry
from tests.settings import TEST_DATABASE_URL

database_uri = TEST_DATABASE_URL
client = Registry(database_uri)


@pytest.fixture(scope="session")
def anyio_backend():
    return ("asyncio", {"debug": False})


@pytest.fixture(scope="session", autouse=True)
async def registry_lifecycle() -> typing.AsyncGenerator:
    yield
    await client.close()


@pytest.fixture(autouse=True)
async def test_database() -> typing.AsyncGenerator:
    await client.drop_database("test_db")
    yield
    await client.drop_database("test_db")
