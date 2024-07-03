from typing import Any, ClassVar, Dict, List, Mapping, Tuple, Type, TypeVar, Union, cast

import bson
import pydantic
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel

from mongoz.core.connection.collections import Collection
from mongoz.core.db.documents.document_row import DocumentRow
from mongoz.core.db.documents.metaclasses import EmbeddedModelMetaClass
from mongoz.core.db.fields.base import MongozField
from mongoz.exceptions import InvalidKeyError, MongozException
from mongoz.utils.mixins import is_operation_allowed

T = TypeVar("T", bound="Document")


class Document(DocumentRow):
    """
    Representation of an Mongoz Document.
    """

    async def create(
        self: "Document", collection: Union[AsyncIOMotorCollection, None] = None
    ) -> "Document":
        """
        Inserts a document.
        """
        is_operation_allowed(self)

        await self.signals.pre_save.send(sender=self.__class__, instance=self)

        data = self.model_dump(exclude={"id"})
        if collection is not None:
            result = await collection.insert_one(data)
        else:
            if isinstance(self.meta.collection, Collection):
                result = await self.meta.collection._collection.insert_one(data)  # noqa
        self.id = result.inserted_id

        await self.signals.post_save.send(sender=self.__class__, instance=self)
        return self

    async def update(
        self, collection: Union[AsyncIOMotorCollection, None] = None, **kwargs: Any
    ) -> "Document":
        """
        Updates a record on an instance level.
        """
        collection = collection or self.meta.collection._collection  # type: ignore
        field_definitions = {
            name: (annotations, ...)
            for name, annotations in self.__annotations__.items()
            if name in kwargs
        }

        if field_definitions:
            pydantic_model: Type[BaseModel] = pydantic.create_model(
                self.__class__.__name__,
                __config__=self.model_config,
                **field_definitions,
            )
            model = pydantic_model.model_validate(kwargs)
            values = model.model_dump()

            # Model data
            data = self.model_dump(exclude={"id": "_id"})
            data.update(values)

            await self.signals.pre_update.send(sender=self.__class__, instance=self)
            await collection.update_one({"_id": self.id}, {"$set": data})
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
    def get_collection(
        cls, collection: Union[AsyncIOMotorCollection, None] = None
    ) -> AsyncIOMotorCollection:
        """
        Get the collection object associated with the document class.
        """
        return collection if collection is not None else cls.meta.collection._collection  # type: ignore

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
        """
        Create indexes defined for the collection or drop for existing ones.

        This method creates indexes defined for the collection associated with the document class.
        It checks if the operation is allowed for the class and then creates the indexes using the
        `create_indexes` method of the collection.

        Returns:
            A list of strings representing the names of the created indexes.

        """
        is_operation_allowed(cls)
        return await cls.meta.collection._collection.create_indexes(cls.meta.indexes)  # type: ignore

    @classmethod
    async def create_indexes_for_multiple_databases(
        cls, database_names: Union[List[str], Tuple[str]]
    ) -> None:
        """
        Create indexes for multiple databases.

        Args:
            database_names (Union[List[str], Tuple[str]]): List or tuple of database names.

        Raises:
            MongozException: If database_names is not a list or tuple.

        Note:
            This method creates indexes for multiple databases. It iterates over the provided
            database names and retrieves the corresponding database and collection objects.
            Then it calls the `create_indexes` method on the collection object with the indexes
            defined in the meta class of the document.

            If `autogenerate_index` is set to True in the meta class, the database name of the
            document is also added to the list of database names.

        Example:
            ```
            Document.create_indexes_for_multiple_databases(["db1", "db2"])
            ```
        """
        is_operation_allowed(cls)

        if not isinstance(database_names, (list, tuple)):
            raise MongozException(detail="Database names must be a list or tuple")

        database_names = list(database_names)
        if not cls.meta.autogenerate_index:
            database_names.append(cls.meta.database.name)  # type: ignore

        for database_name in database_names:
            database = cls.meta.registry.get_database(database_name)  # type: ignore
            collection = database.get_collection(cls.meta.collection.name)  # type: ignore
            await collection._collection.create_indexes(cls.meta.indexes)

    @classmethod
    async def drop_indexes_for_multiple_databases(
        cls, database_names: Union[List[str], Tuple[str]]
    ) -> None:
        """
        Drops indexes for multiple databases.

        Args:
            database_names (Union[List[str], Tuple[str]]): List or tuple of database names.

        Raises:
            MongozException: If database_names is not a list or tuple.

        Note:
            This method drops indexes for multiple databases. It iterates over the provided
            database names and retrieves the corresponding database and collection objects.
            Then it calls the `drop_index` method on the collection object with the indexes
            defined in the meta class of the document.

        Example:
            ```
            Document.create_indexes_for_multiple_databases(["db1", "db2"])
            ```
        """
        is_operation_allowed(cls)

        if not isinstance(database_names, (list, tuple)):
            raise MongozException(detail="Database names must be a list or tuple")

        database_names = list(database_names)
        if not cls.meta.autogenerate_index:
            database_names.append(cls.meta.database.name)  # type: ignore

        for database_name in database_names:
            database = cls.meta.registry.get_database(database_name)  # type: ignore
            collection = database.get_collection(cls.meta.collection.name)  # type: ignore
            await cls.check_indexes(force_drop=True, collection=collection)

    @classmethod
    async def list_indexes(cls) -> List[Dict[str, Any]]:
        """
        List all indexes in the collection.

        This method retrieves all the indexes defined in the collection associated with the document class.
        It checks if the operation is allowed for the class and then uses the `list_indexes` method of the
        collection object to fetch the indexes.

        Returns:
            A list of dictionaries representing the indexes in the collection.

        """
        is_operation_allowed(cls)

        collection_indexes = []

        async for index in cls.meta.collection._collection.list_indexes():  # type: ignore
            collection_indexes.append(index)
        return collection_indexes

    @classmethod
    async def check_indexes(
        cls,
        force_drop: bool = False,
        collection: Union[AsyncIOMotorCollection, None] = None,
    ) -> None:
        """
        Check the indexes defined in the Meta object and perform any possible drop operation.

        This method checks if the indexes defined in the Meta object are present in the collection.
        If an index is defined in the Meta object but not present in the collection, it performs a drop operation
        to remove the index from the collection.

        Args:
            cls: The class object.

        Returns:
            None
        """
        is_operation_allowed(cls)

        # Creates the indexes defined in the Meta object
        if not force_drop:
            await cls.create_indexes()

        collection = cls.get_collection(collection)

        # Get the names of indexes in the collection
        collection_indexes = {index["name"] for index in await cls.list_indexes()}

        # Get the names of indexes defined in the Meta object
        document_index_names = {index.name for index in cls.meta.indexes}

        # Find the indexes that are present in one set but not in the other
        symmetric_difference = collection_indexes.symmetric_difference(document_index_names)

        # Remove the "_id_" index from the symmetric difference
        symmetric_difference.discard("_id_")

        # Drop the indexes that are present in the collection but not in the Meta object
        for name in symmetric_difference:
            await collection.drop_index(name)

        # Check if the indexes defined in the Meta object are present in the collection
        # And perform any possible drop operation
        for name in collection_indexes:
            if name in symmetric_difference:
                continue
            if (
                cls.model_fields.get(name, None) is not None
                and not cls.model_fields.get(name).index  # type: ignore
            ):
                await cls.drop_index(name, collection)

    async def delete(self, collection: Union[AsyncIOMotorCollection, None] = None) -> int:
        """Delete the document."""
        is_operation_allowed(self)

        collection = collection or self.meta.collection._collection  # type: ignore
        await self.signals.pre_delete.send(sender=self.__class__, instance=self)

        result = await collection.delete_one({"_id": self.id})
        await self.signals.post_delete.send(sender=self.__class__, instance=self)
        return cast(int, result.deleted_count)

    @classmethod
    async def drop_index(
        cls, name: str, collection: Union[AsyncIOMotorCollection, None] = None
    ) -> str:
        """Drop single index from Meta indexes by name.

        Can raise `pymongo.errors.OperationFailure`.
        """
        is_operation_allowed(cls)
        collection = cls.get_collection(collection)

        for index in cls.meta.indexes:
            if index.name == name:
                await collection.drop_index(name)
                return name
        raise InvalidKeyError(f"Unable to find index: {name}")

    @classmethod
    async def drop_indexes(
        cls, force: bool = False, collection: Union[AsyncIOMotorCollection, None] = None
    ) -> Union[List[str], None]:
        """Drop all indexes defined for the collection.

        With `force=True`, even indexes not defined on the collection will be removed.
        """
        is_operation_allowed(cls)

        collection = cls.get_collection(collection)
        if force:
            await collection.drop_indexes()
            return None
        index_names = [await cls.drop_index(index.name) for index in cls.meta.indexes]
        return index_names

    async def save(
        self: "Document", collection: Union[AsyncIOMotorCollection, None] = None
    ) -> "Document":
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
        collection = collection or self.meta.collection._collection  # type: ignore

        if not self.id:
            return await self.create()

        await self.signals.pre_save.send(sender=self.__class__, instance=self)

        await collection.update_one(
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

    model_config: ClassVar[pydantic.ConfigDict] = pydantic.ConfigDict(arbitrary_types_allowed=True)
    __mongoz_fields__: ClassVar[Mapping[str, Type["MongozField"]]]
