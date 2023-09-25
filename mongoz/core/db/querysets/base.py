from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, Generic, List, Type, TypeVar, Union

import pydantic

from mongoz.core.db.datastructures import Order
from mongoz.core.db.fields import base
from mongoz.core.db.querysets.expressions import Expression, SortExpression
from mongoz.exceptions import DocumentNotFound, MultipleDumentsReturned
from mongoz.protocols.queryset import QuerySetProtocol

if TYPE_CHECKING:
    from mongoz.core.db.documents import Document

T = TypeVar("T", bound="Document")


class QuerySet(QuerySetProtocol, Generic[T]):
    def __init__(
        self,
        model_class: Type[T],
        filter_by: List[Expression] = None,
    ) -> None:
        self.model_class = model_class
        self._collection = model_class.meta.collection._collection
        self._filter: List[Expression] = filter_by or []
        self._limit_count = 0
        self._skip_count = 0
        self._sort: List[SortExpression] = []

    async def __aiter__(self) -> AsyncGenerator[T, None]:
        filter_query = Expression.compile_many(self._filter)
        cursor = self._collection.find(filter_query)

        async for document in cursor:
            yield self.model_class(**document)

    async def all(self) -> List[T]:
        """
        Returns all the results for a given collection of a document
        """
        filter_query = Expression.compile_many(self._filter)
        cursor = self._collection.find(filter_query)

        if self._sort:
            sort_query = [expr.compile() for expr in self._sort]
            cursor = cursor.sort(sort_query)

        if self._skip_count:
            cursor = cursor.skip(self._skip_count)

        if self._limit_count:
            cursor = cursor.limit(self._limit_count)

        return [self.model_class(**document) async for document in cursor]

    async def count(self) -> int:
        """
        Counts all the documents for a given colletion.
        """

        filter_query = Expression.compile_many(self._filter)
        return await self._collection.count_documents(filter_query)

    async def delete(self) -> int:
        """Delete documents matching the criteria."""
        filter_query = Expression.compile_many(self._filter)
        result = await self._collection.delete_many(filter_query)

        return result.deleted_count

    async def first(self) -> Union[T, None]:
        """
        Returns the first document of a matching criteria.
        """

        objects = await self.limit(1).all()
        if not objects:
            return None
        return objects[0]

    async def last(self) -> Union[T, None]:
        """
        Returns the last document of a matching criteria.
        """
        objects = await self.all()
        if not objects:
            return None
        return objects[-1]

    async def get(self) -> T:
        objects = await self.limit(2).all()
        if len(objects) == 0:
            raise DocumentNotFound()
        elif len(objects) == 2:
            raise MultipleDumentsReturned()
        return objects[0]

    async def get_or_create(self, defaults: Union[Dict[str, Any], None] = None) -> T:
        if not defaults:
            defaults = {}

        data = {expression.key: expression.value for expression in self._filter}
        defaults = {
            (key if isinstance(key, str) else key._name): value for key, value in defaults.items()
        }

        try:
            values = {**defaults, **data}
            self.model_class(**values)
        except ValueError as e:
            raise e

        model = await self._collection.find_one_and_update(
            data,
            {"$setOnInsert": values},
            upsert=True,
            return_document=True,
        )
        return self.model_class(**model)

    def limit(self, count: int = 0) -> "QuerySet[T]":
        self._limit_count = count
        return self

    def skip(self, count: int = 0) -> "QuerySet[T]":
        self._skip_count = count
        return self

    def sort(self, key: Any, direction: Union[Order, None] = None) -> "QuerySet[T]":
        """Sort by (key, direction) or [(key, direction)]."""

        direction = direction or Order.ASCENDING

        if isinstance(key, list):
            for key_dir in key:
                sort_expression = SortExpression(*key_dir)
                self._sort.append(sort_expression)
        elif isinstance(key, (str, base.MongozField)):
            sort_expression = SortExpression(key, direction)
            self._sort.append(sort_expression)
        else:
            self._sort.append(key)
        return self

    def query(self, *args: Union[bool, Dict, Expression]) -> "QuerySet[T]":
        for arg in args:
            assert isinstance(arg, (dict, Expression)), "Invalid argument to Query"
            if isinstance(arg, dict):
                query_expressions = Expression.unpack(arg)
                self._filter.extend(query_expressions)
            else:
                self._filter.append(arg)
        return self

    async def update(self, **kwargs: Any) -> List[T]:
        field_definitions = {
            name: (annotations, ...)
            for name, annotations in self.model_class.__annotations__.items()
            if name in kwargs
        }

        if field_definitions:
            pydantic_model: Type[pydantic.BaseModel] = pydantic.create_model(
                __model_name=self.model_class.__name__,
                __config__=self.model_class.model_config,
                **field_definitions,
            )
            model = pydantic_model.model_validate(kwargs)
            values = model.model_dump()

            filter_query = Expression.compile_many(self._filter)
            await self._collection.update_many(filter_query, {"$set": values})

            _filter = [expression for expression in self._filter if expression.key not in values]
            _filter.extend([Expression(key, "$eq", value) for key, value in values.items()])

            self._filter = _filter
        return await self.all()
