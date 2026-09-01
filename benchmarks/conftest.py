import os

import pytest

from mongoz.core.connection.registry import Registry

database_uri = os.environ.get("DATABASE_URI", "mongodb://root:mongoadmin@localhost:27017")
client = Registry(database_uri)


@pytest.fixture(scope="module")
def anyio_backend():
    return ("asyncio", {"debug": False})
