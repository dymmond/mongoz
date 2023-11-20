from motor.motor_asyncio import AsyncIOMotorCollection


class Collection:
    """
    MongoDB collection object referencing Motor collection
    """

    def __init__(self, name: str, collection: AsyncIOMotorCollection) -> None:
        self._collection: AsyncIOMotorCollection = collection
        self.name = name
