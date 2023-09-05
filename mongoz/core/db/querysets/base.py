from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, Generic, List, Type, TypeVar, Union

from mongoz.core.db.datastructures import Order
from mongoz.core.db.fields.base import BaseField
from mongoz.core.db.querysets.expressions import Expression, SortExpression
from mongoz.exceptions import MultipleObjectsReturned, ObjectNotFound
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
        """Gets the document of a matching criteria."""

        objects = await self.limit(2).all()
        if len(objects) == 0:
            raise ObjectNotFound()
        elif len(objects) == 2:
            raise MultipleObjectsReturned()
        return objects[0]

    async def get_or_create(self, defaults: Union[Dict[str, Any], None]) -> T:
        if not defaults:
            defaults = {}

        data = {expression.key: expression.value for expression in self._filter}
        defaults = {
            (key if isinstance(key, str) else key.name): value for key, value in defaults.items()
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
        elif isinstance(key, (str, BaseField)):
            sort_expression = SortExpression(key, direction)
            self._sort.append(sort_expression)
        else:
            self._sort.append(key)
        return self
