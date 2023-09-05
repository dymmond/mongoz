import asyncio
import os

import pytest

from mongoz import Registry

pytestmark = pytest.mark.asyncio

database_uri = os.environ.get("DATABASE_URI", "mongodb://localhost:27017")
client = Registry(database_uri, get_event_loop=asyncio.get_running_loop)
db = client.get_database("test_db")
