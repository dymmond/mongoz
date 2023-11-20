from typing import Any, Dict, List, Optional

from bson import CodecOptions, UuidRepresentation
from motor.motor_asyncio import AsyncIOMotorDatabase

from mongoz.core.connection.collections import Collection


class Database:
    """
    MongoDB database object referencing Motor database
    """

    def __init__(
        self,
        name: str,
        database: AsyncIOMotorDatabase,
        codec_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._db = database
        self.name = name

        self._codec_options = (
            codec_options
            if codec_options
            else {"uuid_representation": UuidRepresentation.STANDARD}
        )

    @property
    def codec_options(self) -> CodecOptions:
        return CodecOptions(**self._codec_options)

    def get_collection(self, name: str) -> Collection:
        collection = self._db.get_collection(name, codec_options=self.codec_options)
        return Collection(name, collection=collection)

    async def get_collections(self) -> List[Collection]:
        collections = await self._db.list_collection_names()
        return list(map(self.get_collection, collections))
