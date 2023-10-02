from typing import Any, ClassVar, List, Mapping, Type, TypeVar, Union, cast

import bson
import pydantic
from bson.errors import InvalidId
from pydantic import BaseModel

from mongoz.core.db.documents.document_row import DocumentRow
from mongoz.core.db.documents.metaclasses import EmbeddedModelMetaClass
from mongoz.core.db.fields.base import MongozField
from mongoz.exceptions import InvalidKeyError
from mongoz.utils.mixins import is_operation_allowed

T = TypeVar("T", bound="Document")


class Document(DocumentRow):
    """
    Representation of an Mongoz Document.
    """

    async def create(self: "Document") -> "Document":
        """
        Inserts a document.
        """
        is_operation_allowed(self)

        await self.signals.pre_save.send(sender=self.__class__, instance=self)

        data = self.model_dump(exclude={"id"})
        result = await self.meta.collection._collection.insert_one(data)  # type: ignore
        self.id = result.inserted_id

        await self.signals.post_save.send(sender=self.__class__, instance=self)
        return self

    async def update(self, **kwargs: Any) -> "Document":
        """
        Updates a record on an instance level.
        """
        field_definitions = {
            name: (annotations, ...)
            for name, annotations in self.__annotations__.items()
            if name in kwargs
        }

        if field_definitions:
            pydantic_model: Type[BaseModel] = pydantic.create_model(
                __model_name=self.__class__.__name__,
                __config__=self.model_config,
                **field_definitions,
            )
            model = pydantic_model.model_validate(kwargs)
            values = model.model_dump()

            # Model data
            data = self.model_dump(exclude={"id": "_id"})
            data.update(values)

            await self.signals.pre_update.send(sender=self.__class__, instance=self)
            await self.meta.collection._collection.update_one({"_id": self.id}, {"$set": data})  # type: ignore
            await self.signals.post_update.send(sender=self.__class__, instance=self)

            for k, v in data.items():
                setattr(self, k, v)
        return self

    @classmethod
    async def create_many(cls: Type["Document"], models: List["Document"]) -> List["Document"]:
        """
        Insert many documents
        """
        is_operation_allowed(cls)

        if not all(isinstance(model, cls) for model in models):
            raise TypeError(f"All models must be of type {cls.__name__}")

        data = (model.model_dump(exclude={"id"}) for model in models)
        results = await cls.meta.collection._collection.insert_many(data)  # type: ignore
        for model, inserted_id in zip(models, results.inserted_ids, strict=True):
            model.id = inserted_id
        return models

    @classmethod
    async def create_index(cls, name: str) -> str:
        """
        Creates an index from the list of indexes of the Meta object.
        """
        is_operation_allowed(cls)

        for index in cls.meta.indexes:
            if index.name == name:
                await cls.meta.collection._collection.create_indexes([index])  # type: ignore
                return index.name
        raise InvalidKeyError(f"Unable to find index: {name}")

    @classmethod
    async def create_indexes(cls) -> List[str]:
        """Create indexes defined for the collection."""
        is_operation_allowed(cls)

        return await cls.meta.collection._collection.create_indexes(cls.meta.indexes)  # type: ignore

    async def delete(self) -> int:
        """Delete the document."""
        is_operation_allowed(self)

        await self.signals.pre_delete.send(sender=self.__class__, instance=self)

        result = await self.meta.collection._collection.delete_one({"_id": self.id})  # type: ignore

        await self.signals.post_delete.send(sender=self.__class__, instance=self)
        return cast(int, result.deleted_count)

    @classmethod
    async def drop_index(cls, name: str) -> str:
        """Drop single index from Meta indexes by name.

        Can raise `pymongo.errors.OperationFailure`.
        """
        is_operation_allowed(cls)

        for index in cls.meta.indexes:
            if index.name == name:
                await cls.meta.collection._collection.drop_index(name)  # type: ignore
                return name
        raise InvalidKeyError(f"Unable to find index: {name}")

    @classmethod
    async def drop_indexes(cls, force: bool = False) -> Union[List[str], None]:
        """Drop all indexes defined for the collection.

        With `force=True`, even indexes not defined on the collection will be removed.
        """
        is_operation_allowed(cls)

        if force:
            return await cls.meta.collection._collection.drop_indexes()  # type: ignore
        index_names = [await cls.drop_index(index.name) for index in cls.meta.indexes]
        return index_names

    async def save(self: "Document") -> "Document":
        """Save the document.

        This is equivalent of a single instance update.

        When saving the document, if an ID is not provided or it is None,
        it will create a new docuemnt. These scenarios happen when for instance
        a copy of the object is needed on save().

        E.g.:

            movie = await Movie(name="Avengers", year=2019).create()

            # Making a copy of the object and save
            movie.id = None
            await movie.save()
        """
        is_operation_allowed(self)

        if not self.id:
            return await self.create()

        await self.signals.pre_save.send(sender=self.__class__, instance=self)

        await self.meta.collection._collection.update_one(  # type: ignore
            {"_id": self.id}, {"$set": self.model_dump(exclude={"id", "_id"})}
        )
        for k, v in self.model_dump(exclude={"id"}).items():
            setattr(self, k, v)

        await self.signals.post_save.send(sender=self.__class__, instance=self)
        return self

    @classmethod
    async def get_document_by_id(cls: Type[T], id: Union[str, bson.ObjectId]) -> "Document":
        is_operation_allowed(cls)

        if isinstance(id, str):
            try:
                id = bson.ObjectId(id)
            except InvalidId as e:
                raise InvalidKeyError(f'"{id}" is not a valid ObjectId') from e

        return await cls.query({"_id": id}).get()

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"


class EmbeddedDocument(BaseModel, metaclass=EmbeddedModelMetaClass):
    """
    Graphical representation of an Embedded document.
    """

    __mongoz_fields__: ClassVar[Mapping[str, Type["MongozField"]]]
