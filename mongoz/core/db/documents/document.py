from typing import ClassVar, List, Sequence, Type, Union

from pydantic import BaseModel

# from mongoz.core.db.documents.row import ModelRow
from mongoz.core.db.documents.base import MongozBaseModel
from mongoz.core.db.documents.metaclasses import EmbeddedModelMetaClass
from mongoz.exceptions import InvalidKeyError


class Document(MongozBaseModel):
    """
    Representation of an Mongoz Document.
    """

    __embedded__: ClassVar[bool] = False

    async def create(self: Type["Document"]) -> Type["Document"]:
        """
        Inserts a document.
        """
        data = self.model_dump(exclude={"id"})
        result = await self.meta.collection._collection.insert_one(data)
        self.id = result.inserted_id
        return self

    @classmethod
    async def create_many(
        cls: Type["Document"], models: Sequence[Type["Document"]]
    ) -> List[Type["Document"]]:
        """
        Insert many documents
        """
        if not all(isinstance(model, cls) for model in models):
            raise TypeError(f"All models must be of type {cls.__name__}")

        data = {model.model_dump(exclude={"id"}) for model in models}
        results = await cls.meta.collection._collection.insert_many(data)
        for model, inserted_id in zip(models, results.inserted_ids, strict=True):
            model.id = inserted_id
        return models

    @classmethod
    async def create_index(cls, name: str) -> str:
        """
        Creates an index from the list of indexes of the Meta object.
        """
        for index in cls.meta.indexes:
            if index.name == name:
                await cls.meta.collection._collection.create_indexes([index])
                return index.name
        raise IndentationError(f"Unable to find index: {name}")

    @classmethod
    async def create_indexes(cls) -> List[str]:
        """Create indexes defined for the collection."""
        return await cls.meta.collection._collection.create_indexes(cls.meta.indexes)

    async def delete(self) -> int:
        """Delete the document."""
        result = await self.meta.collection._collection.delete_one({"_id": self.id})
        return result.deleted_count

    @classmethod
    async def drop_index(cls, name: str) -> str:
        """Drop single index from Meta indexes by name.

        Can raise `pymongo.errors.OperationFailure`.
        """

        for index in cls.meta.indexes:
            if index.name == name:
                await cls.meta.collection._collection.drop_index(name)
                return name
        raise InvalidKeyError(f"Unable to find index: {name}")

    @classmethod
    async def drop_indexes(cls, force: bool = False) -> Union[List[str], None]:
        """Drop all indexes defined for the collection.

        With `force=True`, even indexes not defined on the collection will be removed.
        """
        if force:
            return await cls.meta.collection._collection.drop_indexes()
        index_names = [await cls.drop_index(index.name) for index in cls.meta.indexes]
        return index_names

    async def save(self: Type["Document"]) -> Type["Document"]:
        """Save the document.

        This is equivalent of a single instance update.
        """

        await self.meta.collection._collection.update_one(
            {"_id": self.id}, {"$set": self.model_dump(exclude={"id", "_id"})}
        )
        for k, v in self.model_dump(exclude={"id"}).items():
            setattr(self, k, v)
        return self

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"


class EmbeddedDocument(BaseModel, metaclass=EmbeddedModelMetaClass):
    """
    Graphical representation of an Embedded document.
    """

    __embedded__: ClassVar[bool] = True
