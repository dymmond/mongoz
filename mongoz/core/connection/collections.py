from __future__ import annotations

from typing import Any, Dict

from pymongo.asynchronous.collection import AsyncCollection


class Collection:
    """
    MongoDB collection object referencing a PyMongo Async collection.
    """

    def __init__(self, name: str, collection: AsyncCollection[Dict[str, Any]]) -> None:
        self._collection = collection
        self.name = name

    @property
    def driver(self) -> AsyncCollection[Dict[str, Any]]:
        """Expose the registry-owned native PyMongo Async collection."""
        return self._collection
