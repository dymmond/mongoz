from typing import List

from motor.motor_asyncio import AsyncIOMotorDatabase

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

    async def get_collections(self) -> List[Collection]:
        collections = await self._db.list_collection_names()
        return list(map(self.get_collection, collections))
