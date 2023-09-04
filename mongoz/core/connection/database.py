import asyncio
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple, Union

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from mongoz.core.connection.collections import Collection


class Database:
    """
    MongoDB database object referencing Motor database
    """

    def __init__(self, name: str, database: AsyncIOMotorDatabase) -> None:
        self._db = database
        self.name = name

    def get_collection(self, name: str) -> Collection:
        collection = self._db.get_collection(name)
        return Collection(name, collection=collection)
