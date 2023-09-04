import asyncio
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple, Union

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase


class Collection:
    """
    MongoDB collection object referencing Motor collection
    """

    def __init__(self, name: str, collection: AsyncIOMotorCollection) -> None:
        self._collection: AsyncIOMotorCollection = collection
        self.name = name
