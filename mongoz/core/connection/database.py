from __future__ import annotations

import datetime
from typing import Any, Dict, List, Mapping, Optional, TypedDict

from bson import CodecOptions, UuidRepresentation
from bson.codec_options import DatetimeConversion, TypeRegistry
from pymongo.asynchronous.database import AsyncDatabase

from mongoz.core.connection.collections import Collection


class CodecOptionsConfig(TypedDict, total=False):
    """Keyword options accepted by :class:`bson.CodecOptions`."""

    document_class: Optional[type[Mapping[str, Any]]]
    tz_aware: bool
    uuid_representation: Optional[int]
    unicode_decode_error_handler: Optional[str]
    tzinfo: Optional[datetime.tzinfo]
    type_registry: Optional[TypeRegistry]
    datetime_conversion: Optional[DatetimeConversion]


class Database:
    """
    MongoDB database object referencing a PyMongo Async database.
    """

    def __init__(
        self,
        name: str,
        database: AsyncDatabase[Dict[str, Any]],
        codec_options: Optional[CodecOptionsConfig] = None,
    ) -> None:
        self._db = database
        self.name = name

        self._codec_options: CodecOptionsConfig = (
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
