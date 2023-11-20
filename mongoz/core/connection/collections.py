from bson.binary import UuidRepresentation
from motor.motor_asyncio import AsyncIOMotorCollection


class Collection:
    """
    MongoDB collection object referencing Motor collection
    """

    def __init__(self, name: str, collection: AsyncIOMotorCollection) -> None:
        self._collection: AsyncIOMotorCollection = collection
        self.name = name
        self.set_uuid_representation(UuidRepresentation.STANDARD)

    def set_uuid_representation(self, representation: int) -> None:
        self._collection.codec_options.uuid_representation = representation
