import asyncio
import os

import pytest

from mongoz.core.connection.registry import Registry

pytestmark = pytest.mark.asyncio

database_uri = os.environ.get("DATABASE_URI", "mongodb://root:mongoadmin@localhost:27017")
client = Registry(database_uri, event_loop=asyncio.get_running_loop)
db = client.get_database("test_db")
collection = db.get_collection("movies")


async def test_client_class() -> None:
    assert client.host == "localhost"
    assert client.port == 27017

    await client.drop_database("sample")
    await client.drop_database(db)

    databases = await client.get_databases()
    assert "admin" in [db.name for db in databases]


async def test_database_class() -> None:
    collection = await db._db.create_collection("movies")

    collections = await db.get_collections()
    assert collections[0].name == collection.name
