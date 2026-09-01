from __future__ import annotations

from functools import partialmethod
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    List,
    Mapping,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import bson
import pydantic
from bson.errors import InvalidId
from pydantic import BaseModel, PrivateAttr
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.operations import DeleteMany, DeleteOne, InsertOne, ReplaceOne, UpdateMany, UpdateOne
from pymongo.results import BulkWriteResult
from typing_extensions import Self

if TYPE_CHECKING:
    from pymongo.asynchronous.client_session import AsyncClientSession

from mongoz.core.connection.collections import Collection
from mongoz.core.connection.database import Database
from mongoz.core.db.documents.document_row import DocumentRow
from mongoz.core.db.documents.indexes import (
    IndexPlan,
    execute_index_plan,
    plan_indexes as build_index_plan,
)
from mongoz.core.db.documents.metaclasses import EmbeddedModelMetaClass
from mongoz.core.db.documents.persistence import dump_document, validate_update_values
from mongoz.core.db.fields.base import MongozField
from mongoz.core.db.querysets.base import Manager
from mongoz.core.utils.cursors import closing_cursor
from mongoz.core.utils.hashable import make_hashable
from mongoz.exceptions import DocumentNotFound, InvalidKeyError, MongozException
from mongoz.utils.mixins import is_operation_allowed

T = TypeVar("T", bound="Document")
WriteOperation = Union[
    InsertOne[Dict[str, Any]],
    DeleteOne,
    DeleteMany,
    ReplaceOne[Dict[str, Any]],
    UpdateOne,
    UpdateMany,
]


class Document(DocumentRow):
    """
    Representation of an Mongoz Document.
    """

    objects: ClassVar[Manager[Self]] = Manager()
    _mongoz_collection: Union[AsyncCollection, None] = PrivateAttr(default=None)

    async def create(
        self: T,
        collection: Union[AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> T:
        """
        Inserts a document.
        """
        is_operation_allowed(self)

        await self.signals.pre_save.send(sender=self.__class__, instance=self)

        data = dump_document(self)
        collection = type(self).get_collection(collection)
        result = await collection.insert_one(data, session=session)
        self.id = result.inserted_id
        self._mongoz_collection = collection

        await self.signals.post_save.send(sender=self.__class__, instance=self)
        return self

    async def update(
        self: T,
        collection: Union[AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
        **kwargs: Any,
    ) -> T:
        """Atomically patch the supplied model fields on this persisted document."""
        is_operation_allowed(self)
        if collection is None:
            instance_collection = getattr(self, "_mongoz_collection", None)
            if isinstance(instance_collection, AsyncCollection):
                collection = instance_collection
            elif isinstance(self.meta.collection, Collection):
                collection = self.meta.collection._collection
        if not kwargs:
            return self

        values = validate_update_values(type(self), kwargs)
        await self.signals.pre_update.send(sender=self.__class__, instance=self)
        collection = type(self).get_collection(collection)
        result = await collection.update_one(
            {"_id": self.id}, {"$set": values.storage}, session=session
        )
        if result.acknowledged and result.matched_count == 0:
            raise DocumentNotFound()
        for field_name, value in values.attributes.items():
            setattr(self, field_name, value)
        await self.signals.post_update.send(sender=self.__class__, instance=self)
        return self

    @classmethod
    async def create_many(
        cls: Type[T],
        models: List[T],
        collection: Union[Collection, AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> List[T]:
        """
        Insert many documents
        """
        is_operation_allowed(cls)

        if not all(isinstance(model, cls) for model in models):
            raise TypeError(f"All models must be of type {cls.__name__}")

        data = (dump_document(model) for model in models)
        if isinstance(collection, Collection):
            results = await collection._collection.insert_many(data, session=session)
        elif isinstance(collection, AsyncCollection):
            results = await collection.insert_many(data, session=session)
        else:
            results = await cls.get_collection().insert_many(data, session=session)
        for model, inserted_id in zip(models, results.inserted_ids, strict=True):
            model.id = inserted_id
            model._mongoz_collection = cls.get_collection(collection)
        return models

    @classmethod
    async def aggregate(
        cls,
        pipeline: Sequence[Mapping[str, Any]],
        collection: Union[Collection, AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
        **kwargs: Any,
    ) -> List[Mapping[str, Any]]:
        """Run a native MongoDB pipeline and materialize its results safely."""
        is_operation_allowed(cls)
        cursor = await cls.get_collection(collection).aggregate(
            pipeline, session=session, **kwargs
        )
        async with closing_cursor(cursor):
            return [document async for document in cursor]

    @classmethod
    async def bulk_write(
        cls,
        requests: Sequence[WriteOperation],
        collection: Union[Collection, AsyncCollection, None] = None,
        *,
        ordered: bool = True,
        session: Union["AsyncClientSession", None] = None,
    ) -> BulkWriteResult:
        """Execute PyMongo collection-level write models without translating results/errors."""
        is_operation_allowed(cls)
        return await cls.get_collection(collection).bulk_write(
            requests, ordered=ordered, session=session
        )

    @classmethod
    def get_collection(
        cls, collection: Union[Collection, AsyncCollection, None] = None
    ) -> AsyncCollection:
        """
        Get the collection object associated with the document class.
        """
        if isinstance(collection, Collection):
            return collection._collection
        if collection is not None:
            return collection
        if not isinstance(cls.meta.collection, Collection):
            raise RuntimeError(f"Document {cls.__name__} has no configured collection")
        return cls.meta.collection._collection

    @classmethod
    async def create_index(
        cls,
        name: str,
        collection: Union[Collection, AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> str:
        """
        Creates an index from the list of indexes of the Meta object.
        """
        is_operation_allowed(cls)

        for index in cls.meta.indexes:
            if index.name == name:
                await cls.get_collection(collection).create_indexes([index], session=session)
                return index.name
        raise InvalidKeyError(f"Unable to find index: {name}")

    @classmethod
    async def create_indexes(
        cls,
        collection: Union[Collection, AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> List[str]:
        """Create missing declared indexes without performing destructive reconciliation."""
        is_operation_allowed(cls)
        target = cls.get_collection(collection)
        plan = await cls.plan_indexes(target, session=session)
        await execute_index_plan(target, plan, session=session)
        return [index.name for index in cls.meta.indexes]

    @classmethod
    async def create_indexes_for_multiple_databases(
        cls,
        database_names: Union[List[str], Tuple[str]],
        *,
        session: Union["AsyncClientSession", None] = None,
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
            if not isinstance(cls.meta.database, Database):
                raise RuntimeError(f"Document {cls.__name__} has no configured database")
            database_names.append(cls.meta.database.name)

        for database_name in database_names:
            if cls.meta.registry is None or not isinstance(cls.meta.collection, Collection):
                raise RuntimeError(f"Document {cls.__name__} has incomplete database metadata")
            database = cls.meta.registry.get_database(database_name)
            collection = database.get_collection(cls.meta.collection.name)
            await cls.create_indexes(collection._collection, session=session)

    @classmethod
    async def drop_indexes_for_multiple_databases(
        cls,
        database_names: Union[List[str], Tuple[str]],
        *,
        session: Union["AsyncClientSession", None] = None,
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
            if not isinstance(cls.meta.database, Database):
                raise RuntimeError(f"Document {cls.__name__} has no configured database")
            database_names.append(cls.meta.database.name)

        for database_name in database_names:
            if cls.meta.registry is None or not isinstance(cls.meta.collection, Collection):
                raise RuntimeError(f"Document {cls.__name__} has incomplete database metadata")
            database = cls.meta.registry.get_database(database_name)
            collection = database.get_collection(cls.meta.collection.name)
            await cls.drop_indexes(collection=collection._collection, session=session)

    @classmethod
    async def list_indexes(
        cls,
        collection: Union[Collection, AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> List[Mapping[str, Any]]:
        """
        List all indexes in the collection.

        This method retrieves all the indexes defined in the collection associated with the document class.
        It checks if the operation is allowed for the class and then uses the `list_indexes` method of the
        collection object to fetch the indexes.

        Returns:
            A list of dictionaries representing the indexes in the collection.

        """
        is_operation_allowed(cls)

        collection_indexes: List[Mapping[str, Any]] = []
        if isinstance(collection, Collection):
            collection = collection._collection
        elif isinstance(collection, AsyncCollection):
            pass
        else:
            collection = cls.get_collection()

        cursor = await collection.list_indexes(session=session)
        async with closing_cursor(cursor):
            async for index in cursor:
                collection_indexes.append(index)
        return collection_indexes

    @classmethod
    async def plan_indexes(
        cls,
        collection: Union[Collection, AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> IndexPlan:
        """Inspect one collection and return a side-effect-free reconciliation plan."""
        is_operation_allowed(cls)
        existing = await cls.list_indexes(collection, session=session)
        return build_index_plan(cls.meta.indexes, existing)

    @classmethod
    async def check_indexes(
        cls,
        force_drop: bool = False,
        collection: Union[Collection, AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> IndexPlan:
        """Plan and execute safe reconciliation for one collection.

        Missing indexes are created and unmanaged indexes are retained. Same-name definition
        changes require ``force_drop=True``; even then, unrelated names are never deleted.
        """
        is_operation_allowed(cls)

        target = cls.get_collection(collection)
        plan = await cls.plan_indexes(target, session=session)
        await execute_index_plan(target, plan, allow_recreate=force_drop, session=session)
        return plan

    async def delete(
        self,
        collection: Union[AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> int:
        """Delete the document."""
        is_operation_allowed(self)

        if collection is None:
            instance_collection = getattr(self, "_mongoz_collection", None)
            if isinstance(instance_collection, AsyncCollection):
                collection = instance_collection
            elif isinstance(self.meta.collection, Collection):
                collection = self.meta.collection._collection
        await self.signals.pre_delete.send(sender=self.__class__, instance=self)
        collection = type(self).get_collection(collection)
        result = await collection.delete_one({"_id": self.id}, session=session)
        await self.signals.post_delete.send(sender=self.__class__, instance=self)
        return result.deleted_count

    @classmethod
    async def drop_index(
        cls,
        name: str,
        collection: Union[Collection, AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> str:
        """Drop single index from Meta indexes by name.

        Can raise `pymongo.errors.OperationFailure`.
        """
        is_operation_allowed(cls)
        collection = cls.get_collection(collection)

        for index in cls.meta.indexes:
            if index.name == name:
                await collection.drop_index(name, session=session)
                return name
        raise InvalidKeyError(f"Unable to find index: {name}")

    @classmethod
    async def drop_indexes(
        cls,
        force: bool = False,
        collection: Union[Collection, AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> Union[List[str], None]:
        """Drop all indexes defined for the collection.

        With `force=True`, even indexes not defined on the collection will be removed.
        """
        is_operation_allowed(cls)

        collection = cls.get_collection(collection)
        if force:
            await collection.drop_indexes(session=session)
            return None
        index_names = [
            await cls.drop_index(index.name, collection, session=session)
            for index in cls.meta.indexes
        ]
        return index_names

    async def save(
        self: T,
        collection: Union[AsyncCollection, None] = None,
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> T:
        """Save the document.

        This is equivalent of a single instance update.

        This synchronizes every modeled field and can overwrite concurrent changes to those
        fields. Use :meth:`update` for a selected-field patch.

        When saving the document, if an ID is not provided or it is None,
        it will create a new document. These scenarios happen when for instance
        a copy of the object is needed on save().

        E.g.:

            movie = await Movie(name="Avengers", year=2019).create()

            # Making a copy of the object and save
            movie.id = None
            await movie.save()
        """
        is_operation_allowed(self)
        if collection is None:
            instance_collection = getattr(self, "_mongoz_collection", None)
            if isinstance(instance_collection, AsyncCollection):
                collection = instance_collection
            elif isinstance(self.meta.collection, Collection):
                collection = self.meta.collection._collection

        if not self.id:
            return await self.create(collection, session=session)

        await self.signals.pre_save.send(sender=self.__class__, instance=self)

        collection = type(self).get_collection(collection)
        result = await collection.update_one(
            {"_id": self.id},
            {"$set": dump_document(self)},
            session=session,
        )
        if result.acknowledged and result.matched_count == 0:
            raise DocumentNotFound()
        for k, v in self.model_dump(exclude={"id"}).items():
            setattr(self, k, v)

        await self.signals.post_save.send(sender=self.__class__, instance=self)
        return self

    @classmethod
    async def get_document_by_id(
        cls: Type[T],
        id: Union[str, bson.ObjectId],
        *,
        session: Union["AsyncClientSession", None] = None,
    ) -> T:
        is_operation_allowed(cls)

        if isinstance(id, str):
            try:
                id = bson.ObjectId(id)
            except InvalidId as e:
                raise InvalidKeyError(f'"{id}" is not a valid ObjectId') from e

        queryset = cls.query({"_id": id})
        if session is not None:
            return await queryset.using_session(session).get()
        return await queryset.get()

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"


class EmbeddedDocument(BaseModel, metaclass=EmbeddedModelMetaClass):
    """
    Graphical representation of an Embedded document.
    """

    model_config: ClassVar[pydantic.ConfigDict] = pydantic.ConfigDict(arbitrary_types_allowed=True)
    __mongoz_fields__: ClassVar[Mapping[str, "MongozField"]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.get_field_display()
        self.validate_fields_values()

    def _get_field_display(self, field: Type["Document"]) -> str:
        value = getattr(self, field.name)
        choices_dict: Dict = dict(make_hashable(field.choices))
        return choices_dict.get(make_hashable(value), value)

    @classmethod
    def get_field_display(cls) -> None:
        for name, field in cls.model_fields.items():
            if hasattr(field, "choices") and field.choices:
                if "get_%s_display" % name not in cls.__dict__:
                    setattr(
                        cls,
                        "get_%s_display" % name,
                        partialmethod(cls._get_field_display, field=field),
                    )

    def validate_fields_values(self) -> None:
        model_fields = type(self).model_fields
        for field_name, value in self.model_dump().items():
            if field_name in model_fields and not isinstance(value, bson.ObjectId) and value:
                validated_value = model_fields[field_name].validate_field_value(value)
                setattr(self, field_name, validated_value)
