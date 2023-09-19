import pytest
from tests.conftest import client

db = client.get_database("test_db")
collection = db.get_collection("movies")
pytestmark = pytest.mark.asyncio


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
