import typing

import pytest

from mongoz.core.connection.registry import Registry
from tests.settings import TEST_DATABASE_URL

database_uri = TEST_DATABASE_URL
client = Registry(database_uri)


@pytest.fixture(scope="session", autouse=True)
async def index_registry_lifecycle() -> typing.AsyncGenerator:
    yield
    await client.close()


@pytest.fixture(autouse=True)
async def test_database() -> typing.AsyncGenerator:
    yield
    await client.drop_database("test_db")
    await client.drop_database("test_my_db")
    await client.drop_database("test_second_db")
