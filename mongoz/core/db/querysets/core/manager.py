import copy
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Dict,
    Generator,
    Generic,
    List,
    Type,
    TypeVar,
    Union,
    cast,
)

import bson
import pydantic
from bson import Code

from mongoz import settings
from mongoz.core.db.datastructures import Order
from mongoz.core.db.fields import base
from mongoz.core.db.querysets.expressions import Expression, SortExpression
from mongoz.exceptions import DocumentNotFound, MultipleDumentsReturned
from mongoz.protocols.queryset import QuerySetProtocol

if TYPE_CHECKING:
    from mongoz.core.db.documents import Document

T = TypeVar("T", bound="Document")


class Manager(QuerySetProtocol, Generic[T]):
    def __init__(
        self,
        model_class: Union[Type["Document"], None] = None,
        filter_by: List[Expression] = None,
    ) -> None:
        self.model_class = model_class

        if self.model_class:
            self._collection = self.model_class.meta.collection._collection  # type: ignore
        else:
            self._collection = None

        self._filter: List[Expression] = [] if filter_by is None else filter_by
        self._limit_count = 0
        self._skip_count = 0
        self._sort: List[SortExpression] = []

    def clone(self) -> Any:
        manager = self.__class__.__new__(self.__class__)
        manager.model_class = self.model_class
        manager._filter = copy.copy(self._filter)
        manager._limit_count = self._limit_count
        manager._skip_count = self._skip_count
        manager._sort = self._sort
        manager._collection = self._collection
        return manager

    def get_operator(self, name: str) -> Expression:
        """
        Returns the operator for the given filter.
        """
        return settings.get_operator(name)

    async def __aiter__(self) -> AsyncGenerator[T, None]:
        filter_query = Expression.compile_many(self._filter)
        cursor = self._collection.find(filter_query)

        async for document in cursor:
            yield self.model_class(**document)

    async def all(self) -> List[T]:
        """
        Returns all the results for a given collection of a document
        """
        manager: "Manager" = self.clone()

        filter_query = Expression.compile_many(manager._filter)
        cursor = manager._collection.find(filter_query)

        if manager._sort:
            sort_query = [expr.compile() for expr in manager._sort]
            cursor = cursor.sort(sort_query)

        if manager._skip_count:
            cursor = cursor.skip(manager._skip_count)

        if manager._limit_count:
            cursor = cursor.limit(manager._limit_count)

        return [manager.model_class(**document) async for document in cursor]

    # def query(self, *args: Union[bool, Dict, Expression]) -> "QuerySet[T]":
    #     for arg in args:
    #         assert isinstance(arg, (dict, Expression)), "Invalid argument to Query"
    #         if isinstance(arg, dict):
    #             query_expressions = Expression.unpack(arg)
    #             self._filter.extend(query_expressions)
    #         else:
    #             self._filter.append(arg)
    #     return self

    def _find_and_replace_id(self, key: str) -> str:
        """
        Making sure the ID is always parsed as `_id`.
        """

        if key in settings.parsed_ids:
            return self.model_class.id.pydantic_field.alias
        return key

    def filter_query(self, **kwargs: Any) -> "Manager":
        """
        Builds the filter query for the given manager.
        """
        clauses = []
        filter_clauses = self._filter

        for key, value in kwargs.items():
            key = self._find_and_replace_id(key)

            if "__" in key:
                parts = key.split("__")

                # Determine if we should treat the final part as a
                # filter operator or as a related field.
                if parts[-1] in settings.filter_operators:
                    operator = self.get_operator(parts[-1])
                    parts[-2]
                    parts[:-2]
                else:
                    operator = self.get_operator("exact")
                    parts[-1]
                    parts[:-1]
            else:
                operator = self.get_operator("exact")
                expression = operator(key, value)
                clauses.append(expression)

            filter_clauses += clauses

        return cast(
            "Manager", self.__class__(model_class=self.model_class, filter_by=filter_clauses)
        )

    def filter(self, clause: Union[str, List[Expression], None] = None, **kwargs) -> "Manager":
        """
        Filters the queryset based on the given clauses.
        """
        manager: "Manager" = self.clone()

        if clause is None:
            return manager.filter_query(**kwargs)
        manager._filter.append(clause)
        return manager

    async def count(self) -> int:
        """
        Counts all the documents for a given colletion.
        """
        manager: "Manager" = self.clone()

        filter_query = Expression.compile_many(manager._filter)
        return cast(int, await manager._collection.count_documents(filter_query))

    async def create(self, **kwargs: Any) -> "Document":
        """
        Creates a mongo db document.
        """
        manager: "Manager" = self.clone()
        instance = await manager.model_class(**kwargs).create()
        return instance

    async def delete(self) -> int:
        """Delete documents matching the criteria."""
        manager: "Manager" = self.clone()
        filter_query = Expression.compile_many(manager._filter)
        result = await manager._collection.delete_many(filter_query)

        return cast(int, result.deleted_count)

    async def first(self) -> Union[T, None]:
        """
        Returns the first document of a matching criteria.
        """
        manager: "Manager" = self.clone()

        objects = await manager.limit(1).all()
        if not objects:
            return None
        return objects[0]

    async def last(self) -> Union[T, None]:
        """
        Returns the last document of a matching criteria.
        """
        manager: "Manager" = self.clone()
        objects = await manager.all()
        if not objects:
            return None
        return objects[-1]

    async def get(self) -> "Document":
        """
        Gets a document.
        """
        manager: "Manager" = self.clone()

        objects = await manager.limit(2).all()
        if len(objects) == 0:
            raise DocumentNotFound()
        elif len(objects) == 2:
            raise MultipleDumentsReturned()
        return objects[0]

    async def get_or_create(self, defaults: Union[Dict[str, Any], None] = None) -> T:
        manager: "Manager" = self.clone()
        if not defaults:
            defaults = {}

        data = {expression.key: expression.value for expression in manager._filter}
        defaults = {
            (key if isinstance(key, str) else key._name): value for key, value in defaults.items()
        }

        try:
            values = {**defaults, **data}
            manager.model_class(**values)
        except ValueError as e:
            raise e

        model = await manager._collection.find_one_and_update(
            data,
            {"$setOnInsert": values},
            upsert=True,
            return_document=True,
        )
        return manager.model_class(**model)

    async def distinct_values(self, key: str) -> List[Any]:
        """
        Returns a list of distinct values filtered by the key.
        """
        filter_query = Expression.compile_many(self._filter)
        values = await self._collection.find(filter_query).distinct(key=key)
        return cast(List[Any], values)

    async def where(self, condition: Union[str, Code]) -> Any:
        """
        Adds a $where clause to the query.

        E.g.: Movie.objects.where('this.a < (this.b + this.c)')
        """
        assert isinstance(
            condition, (str, Code)
        ), "The where clause must be a string or a bson.Code"

        manager: "Manager" = self.clone()

        filter_query = Expression.compile_many(manager._filter)
        cursor = manager._collection.find(filter_query).where(condition)
        return [manager.model_class(**document) async for document in cursor]

    def limit(self, count: int = 0) -> "Manager[T]":
        manager: "Manager" = self.clone()
        manager._limit_count = count
        return manager

    def skip(self, count: int = 0) -> "Manager[T]":
        manager: "Manager" = self.clone()
        manager._skip_count = count
        return manager

    def sort(self, key: Any, direction: Union[Order, None] = None) -> "Manager[T]":
        """Sort by (key, direction) or [(key, direction)]."""
        manager: "Manager" = self.clone()

        direction = direction or Order.ASCENDING

        if isinstance(key, list):
            for key_dir in key:
                sort_expression = SortExpression(*key_dir)
                manager._sort.append(sort_expression)
        elif isinstance(key, (str, base.MongozField)):
            sort_expression = SortExpression(key, direction)
            manager._sort.append(sort_expression)
        else:
            manager._sort.append(key)
        return manager

    # def query(self, *args: Union[bool, Dict, Expression]) -> "QuerySet[T]":
    #     for arg in args:
    #         assert isinstance(arg, (dict, Expression)), "Invalid argument to Query"
    #         if isinstance(arg, dict):
    #             query_expressions = Expression.unpack(arg)
    #             self._filter.extend(query_expressions)
    #         else:
    #             self._filter.append(arg)
    #     return self

    async def update_many(self, **kwargs: Any) -> List[T]:
        """
        Updates many documents (bulk update)
        """
        manager: "Manager" = self.clone()

        field_definitions = {
            name: (annotations, ...)
            for name, annotations in manager.model_class.__annotations__.items()
            if name in kwargs
        }

        if field_definitions:
            pydantic_model: Type[pydantic.BaseModel] = pydantic.create_model(
                __model_name=manager.model_class.__name__,
                __config__=manager.model_class.model_config,
                **field_definitions,
            )
            model = pydantic_model.model_validate(kwargs)
            values = model.model_dump()

            filter_query = Expression.compile_many(manager._filter)
            await manager._collection.update_many(filter_query, {"$set": values})

            _filter = [
                expression for expression in manager._filter if expression.key not in values
            ]
            _filter.extend([Expression(key, "$eq", value) for key, value in values.items()])

            manager._filter = _filter
        return await manager.all()

    async def create_many(self, models: List["Document"]) -> List["Document"]:
        """
        Creates many documents (bulk create).
        """
        manager: "Manager" = self.clone()
        return await manager.model_class.create_many(models=models)

    async def get_document_by_id(self, id: Union[str, bson.ObjectId]) -> "Document":
        """
        Gets a document by the id
        """
        return await self.model_class.get_document_by_id(id)

    def __await__(
        self,
    ) -> Generator[Any, None, List["Document"]]:
        return self.all().__await__()
