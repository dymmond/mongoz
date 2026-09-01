from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Any, Dict, Sequence, Tuple, Type, Union

from pymongo import AsyncMongoClient

from mongoz.core.connection.database import Database

if TYPE_CHECKING:
    from mongoz import Document


class Registry:
    """
    Own the reusable PyMongo Async client for a group of documents.

    A registry creates exactly one client. PyMongo binds that client to the
    event loop of its first network operation and rejects use from another
    loop. Closing a registry is final; create a new registry to reconnect.
    """

    def __init__(self, url: str) -> None:
        self.url = url
        self._client: AsyncMongoClient[Dict[str, Any]] = AsyncMongoClient(self.url)
        self._closed = False
        self.documents: Dict[str, Type["Document"]] = {}

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("Registry is closed and cannot be reused")

    @property
    async def address(self) -> Union[Tuple[str, int], None]:
        """Return the connected server address, if one is available."""
        self._ensure_open()
        return await self._client.address

    @property
    def host(self) -> str:
        return self._client.HOST

    @property
    def port(self) -> int:
        return self._client.PORT

    @property
    def driver(self) -> AsyncMongoClient[Dict[str, Any]]:
        """Expose the registry-owned native PyMongo Async client."""
        self._ensure_open()
        return self._client

    @property
    def is_closed(self) -> bool:
        return self._closed

    async def close(self) -> None:
        """Close the owned client once; subsequent calls are no-ops."""
        if self._closed:
            return
        await self._client.close()
        self._closed = True

    async def __aenter__(self) -> "Registry":
        self._ensure_open()
        return self

    async def __aexit__(
        self,
        exc_type: Union[Type[BaseException], None],
        exc_value: Union[BaseException, None],
        traceback: Union[TracebackType, None],
    ) -> None:
        try:
            await self.close()
        except BaseException as cleanup_error:
            if exc_value is not None:
                raise exc_value.with_traceback(traceback) from cleanup_error
            raise

    async def drop_database(self, database: Union[str, Database]) -> None:
        """
        Drops an existing mongo db database/
        """
        self._ensure_open()
        if not isinstance(database, Database):
            await self._client.drop_database(database)
        else:
            await self._client.drop_database(database.driver)

    def get_database(self, name: str) -> Database:
        self._ensure_open()
        database = self._client.get_database(name)
        return Database(name=name, database=database)

    async def get_databases(self) -> Sequence[Database]:
        self._ensure_open()
        databases = await self._client.list_database_names()
        return list(map(self.get_database, databases))

    async def document_checks(self) -> None:
        """
        Runs the document checks for all the documents in the registry.
        """
        self._ensure_open()
        for document in self.documents.values():
            await document.check_indexes()
