import asyncio
from typing import TYPE_CHECKING, Callable, Dict, Sequence, Tuple, Union, cast

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from mongoz.core.connection.database import Database

if TYPE_CHECKING:
    from mongoz import Document


class Registry:
    """
    MongoDB client object referencing the Async Motor Client
    """

    def __init__(
        self,
        url: str,
        event_loop: Union[Callable[[], asyncio.AbstractEventLoop], None] = None,
    ) -> None:
        self.event_loop = event_loop or asyncio.get_event_loop
        self.url = url
        self._client: AsyncIOMotorClient = AsyncIOMotorClient(self.url)
        self._client.get_io_loop = self.event_loop  # type: ignore
        self.documents: Dict[str, "Document"] = {}

    @property
    def address(self) -> Tuple[str, int]:
        return cast(Tuple[str, int], self._client.address)

    @property
    def host(self) -> str:
        return self._client.HOST

    @property
    def port(self) -> str:
        return cast(str, self._client.PORT)

    @property
    def driver(self) -> AsyncIOMotorDatabase:
        return self._client.driver

    async def drop_database(self, database: Union[str, Database]) -> None:
        """
        Drops an existing mongo db database/
        """
        if not isinstance(database, Database):
            await self._client.drop_database(database)
        else:
            await self._client.drop_database(database._db)

    def get_database(self, name: str) -> Database:
        database = self._client.get_database(name)
        return Database(name=name, database=database)

    async def get_databases(self) -> Sequence[Database]:
        databases = await self._client.list_database_names()
        return list(map(self.get_database, databases))
