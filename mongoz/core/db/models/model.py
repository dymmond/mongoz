from typing import Any, Dict, List, Optional, Sequence, Set, Type, Union

import bson
from bson.errors import InvalidId

from mongoz.core.db.models.row import ModelRow
from mongoz.core.utils.functional import mongoz_setattr
from mongoz.exceptions import InvalidKeyError, InvalidObjectIdError


class Model(ModelRow):
    """
    Representation of an Mongoz Model.
    This also means it can generate declarative SQLAlchemy models
    from anywhere.
    """

    async def insert(self: Type["Model"]) -> Type["Model"]:
        """
        Inserts a document.
        """
        data = self.model_dump(exclude={"id"})
        result = await self.meta.collection._collection.insert_one(data)
        self.id = result.inserted_id
        return self

    @classmethod
    async def insert_many(
        cls: Type["Model"], models: Sequence[Type["Model"]]
    ) -> List[Type["Model"]]:
        """
        Insert many documents
        """
        if not all(isinstance(model, cls) for model in models):
            raise TypeError(f"All models must be of type {cls.__name__}")

        data = {model.model_dump(exclude={"id"}) for model in models}
        results = await cls.meta.collection._collection.insert_many(data)
        for model, inserted_id in zip(models, results.inserted_ids):
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

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self}>"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.pkname}={self.pk})"

    async def save(self: Type["Model"]) -> Type["Model"]:
        """Save the document.

        This is equivalent of a single instance update.
        """

        await self.meta.collection._collection.update_one(
            {"_id": self.id}, {"$set": self.model_dump(exclude={"id", "_id"})}
        )
        for k, v in self.model_dump(exclude={"id"}).items():
            setattr(self, k, v)
        return self
