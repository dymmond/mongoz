from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Dict,
    Generic,
    List,
    Sequence,
    Set,
    Type,
    TypeVar,
    Union,
    overload,
)

import bson
from bson import Code
from pymongo.asynchronous.cursor import AsyncCursor
from typing_extensions import Literal, Self

from mongoz.core.db.datastructures import Order
from mongoz.core.db.fields import base
from mongoz.core.db.querysets.core.runtime import SessionBoundQuery
from mongoz.core.db.querysets.expressions import (
    Expression,
    SortExpression,
    parse_query_argument,
)
from mongoz.core.utils.cursors import closing_cursor
from mongoz.exceptions import (
    DocumentNotFound,
    FieldDefinitionError,
    MultipleDocumentsReturned,
    OperatorInvalid,
)

if TYPE_CHECKING:
    from pymongo.asynchronous.client_session import AsyncClientSession

    from mongoz.core.db.documents import Document

T = TypeVar("T", bound="Document")


class BaseQuerySet(SessionBoundQuery, Generic[T]):
    def __init__(
        self,
        model_class: Type[T],
        filter_by: Union[List[Expression], None] = None,
        only_fields: Union[str, None] = None,
        defer_fields: Union[str, None] = None,
        session: Union["AsyncClientSession", None] = None,
    ) -> None:
        self.model_class = model_class
        self._collection = model_class.get_collection()
        self._filter: List[Expression] = filter_by or []
        self._limit_count = 0
        self._skip_count = 0
        self._sort: List[SortExpression] = []
        self._only_fields = [] if only_fields is None else only_fields
        self._defer_fields = [] if defer_fields is None else defer_fields
        self._session = session

    def clone(self) -> Self:
        """Return an isolated query derivation with the same execution state."""
        queryset = self.__class__.__new__(self.__class__)
        queryset.model_class = self.model_class
        queryset._collection = self._collection
        queryset._filter = list(self._filter)
        queryset._limit_count = self._limit_count
        queryset._skip_count = self._skip_count
        queryset._sort = list(self._sort)
        queryset._only_fields = list(self._only_fields)
        queryset._defer_fields = list(self._defer_fields)
        queryset._session = self._session
        return queryset

    def validate_only_and_defer(self) -> None:
        if self._only_fields and self._defer_fields:
            raise FieldDefinitionError("You cannot use .only() and .defer() at the same time.")

    def filter_only_and_defer(self, *fields: str, is_only: bool = False) -> Self:
        """
        Filters by the only fields.
        """
        queryset = self.clone()
        queryset.validate_only_and_defer()

        document_fields = list(fields)

        id_attribute = self.model_class.meta.id_attribute
        if not isinstance(id_attribute, str):
            id_attribute = id_attribute.alias or id_attribute.name or "id"
        if id_attribute not in fields and is_only:
            document_fields.insert(0, id_attribute)
        only_or_defer = "_only_fields" if is_only else "_defer_fields"

        setattr(queryset, only_or_defer, document_fields)
        return queryset

    def limit(self, count: int = 0) -> Self:
        queryset = self.clone()
        queryset._limit_count = count
        return queryset

    def skip(self, count: int = 0) -> Self:
        queryset = self.clone()
        queryset._skip_count = count
        return queryset

    def only(self, *fields: str) -> Self:
        """
        Filters by the only fields.
        """
        return self.filter_only_and_defer(*fields, is_only=True)

    def defer(self, *fields: str) -> Self:
        """
        Returns a list of documents with the selected defers fields.
        """
        return self.filter_only_and_defer(*fields, is_only=False)

    def sort(self, key: Any, direction: Union[Order, None] = None) -> Self:
        """Sort by (key, direction) or [(key, direction)]."""
        queryset = self.clone()

        direction = direction or Order.ASCENDING

        if isinstance(key, list):
            for key_dir in key:
                sort_expression = SortExpression(*key_dir)
                queryset._sort.append(sort_expression)
        elif isinstance(key, (str, base.MongozField)):
            sort_expression = SortExpression(key, direction)
            queryset._sort.append(sort_expression)
        else:
            if not isinstance(key, SortExpression):
                raise FieldDefinitionError("Invalid sort expression.")
            queryset._sort.append(key)
        return queryset

    def query(self, *args: Union[bool, Dict[str, Any], Expression]) -> Self:
        queryset = self.clone()
        for arg in args:
            queryset._filter.extend(parse_query_argument(arg, operation="Query"))
        return queryset


class QuerySet(BaseQuerySet[T]):
    def _cursor(self) -> AsyncCursor[Dict[str, Any]]:
        """Build the canonical native cursor for this immutable query state."""
        filter_query = Expression.compile_many(self._filter)
        cursor = self._collection.find(filter_query, **self._driver_options)

        if self._sort:
            cursor = cursor.sort([expr.compile() for expr in self._sort])
        if self._skip_count:
            cursor = cursor.skip(self._skip_count)
        if self._limit_count:
            cursor = cursor.limit(self._limit_count)
        return cursor

    async def __aiter__(self) -> AsyncGenerator[T, None]:
        cursor = self._cursor()
        is_only_fields = bool(self._only_fields)
        is_defer_fields = bool(self._defer_fields)

        async with closing_cursor(cursor):
            async for document in cursor:
                yield self.model_class.from_row(
                    document,
                    is_only_fields=is_only_fields,
                    only_fields=self._only_fields,
                    is_defer_fields=is_defer_fields,
                    defer_fields=self._defer_fields,
                    from_collection=self._collection,
                )

    async def none(self) -> "QuerySet[T]":
        """
        Returns an empty QuerySet
        """
        queryset = self.clone()
        queryset._filter.append(Expression("$expr", "$eq", [1, 0]))
        return queryset

    async def all(self) -> List[T]:
        """
        Returns all the results for a given collection of a document
        """
        cursor = self._cursor()

        # For only fields
        is_only_fields = True if self._only_fields else False
        is_defer_fields = True if self._defer_fields else False

        async with closing_cursor(cursor):
            results: List[T] = [
                self.model_class.from_row(
                    document,
                    is_only_fields=is_only_fields,
                    only_fields=self._only_fields,
                    is_defer_fields=is_defer_fields,
                    defer_fields=self._defer_fields,
                    from_collection=self._collection,
                )
                async for document in cursor
            ]

        return results

    async def count(self) -> int:
        """
        Counts all the documents for a given colletion.
        """

        filter_query = Expression.compile_many(self._filter)
        return await self._collection.count_documents(filter_query, **self._driver_options)

    async def delete(self) -> int:
        """Delete documents matching the criteria."""
        filter_query = Expression.compile_many(self._filter)
        result = await self._collection.delete_many(filter_query, **self._driver_options)

        return result.deleted_count

    async def first(self) -> Union[T, None]:
        """
        Returns the first document of a matching criteria.
        """

        objects: List[T] = await self.limit(1).all()
        if not objects:
            return None
        return objects[0]

    async def last(self) -> Union[T, None]:
        """Return the last result while retaining at most one raw row."""
        cursor = self._cursor()
        last_document: Union[Dict[str, Any], None] = None
        async with closing_cursor(cursor):
            async for document in cursor:
                last_document = document
        if last_document is None:
            return None
        return self.model_class.from_row(
            last_document,
            is_only_fields=bool(self._only_fields),
            only_fields=self._only_fields,
            is_defer_fields=bool(self._defer_fields),
            defer_fields=self._defer_fields,
            from_collection=self._collection,
        )

    async def get(self) -> T:
        objects: List[T] = await self.limit(2).all()
        if len(objects) == 0:
            raise DocumentNotFound()
        elif len(objects) == 2:
            raise MultipleDocumentsReturned()
        return objects[0]

    async def get_or_none(self) -> Union[T, None]:
        """
        Gets a document or returns None.
        """
        objects: List[T] = await self.limit(2).all()
        if len(objects) == 0:
            return None
        elif len(objects) > 1:
            raise MultipleDocumentsReturned()
        return objects[0]

    async def get_or_create(self, defaults: Union[Dict[str, Any], None] = None) -> T:
        from mongoz.core.db.documents.persistence import get_or_create_document

        return await get_or_create_document(
            self.model_class,
            self._collection,
            self._filter,
            defaults or {},
            self._driver_options,
        )

    async def distinct_values(self, key: str) -> List[Any]:
        """
        Returns a list of distinct values filtered by the key.
        """
        filter_query = Expression.compile_many(self._filter)
        values = await self._collection.find(filter_query, **self._driver_options).distinct(
            key=key
        )
        return values

    async def where(self, condition: Union[str, Code]) -> List[T]:
        """
        Adds a $where clause to the query.

        E.g.: Movie.query().where('this.a < (this.b + this.c)')
        """
        if not isinstance(condition, (str, Code)):
            raise OperatorInvalid(
                f"The where clause must be a string or bson.Code; got {type(condition).__name__}."
            )

        filter_query = Expression.compile_many(self._filter)
        cursor = self._collection.find(filter_query, **self._driver_options).where(condition)
        async with closing_cursor(cursor):
            return [self.model_class(**document) async for document in cursor]

    async def bulk_create(self, models: List[T]) -> List[T]:
        """
        Creates many documents (bulk create).
        """
        return await self.model_class.create_many(
            models=models, collection=self._collection, session=self._session
        )

    async def update(self, **kwargs: Any) -> List[T]:
        """
        Updates a document
        """
        return await self.update_many(**kwargs)

    async def bulk_update(self, **kwargs: Any) -> List[T]:
        return await self.update_many(**kwargs)

    async def update_many(self, **kwargs: Any) -> List[T]:
        from mongoz.core.db.documents.persistence import patch_many

        queryset = self.clone()
        if not kwargs:
            return await queryset.all()
        update, identifiers = await patch_many(
            queryset.model_class,
            queryset._collection,
            queryset._filter,
            kwargs,
            queryset._driver_options,
        )
        if not identifiers:
            return []
        queryset._filter = [Expression("_id", "$in", identifiers)]
        queryset._filter.extend(
            Expression(name, "$eq", value) for name, value in update.storage.items()
        )
        return await queryset.all()

    async def get_document_by_id(self, id: Union[str, bson.ObjectId]) -> T:
        """
        Gets a document by the id.
        """
        return await self.model_class.get_document_by_id(id, session=self._session)

    @overload
    async def values(
        self,
        fields: Union[List[str], None] = None,
        exclude: Union[Sequence[str], Set[str], None] = None,
        exclude_none: bool = False,
        flatten: bool = False,
        *,
        __as_tuple__: Literal[False] = False,
    ) -> List[Dict[str, Any]]: ...

    @overload
    async def values(
        self,
        fields: Union[List[str], None] = None,
        exclude: Union[Sequence[str], Set[str], None] = None,
        exclude_none: bool = False,
        flatten: bool = False,
        *,
        __as_tuple__: Literal[True],
    ) -> List[Any]: ...

    async def values(
        self,
        fields: Union[List[str], None] = None,
        exclude: Union[Sequence[str], Set[str], None] = None,
        exclude_none: bool = False,
        flatten: bool = False,
        *,
        __as_tuple__: bool = False,
    ) -> List[Any]:
        """
        Returns the results in a python dictionary format.
        """
        if fields is not None and not isinstance(fields, list):
            raise FieldDefinitionError(detail="Fields must be an iterable.")
        selected_fields = fields or []
        documents = await self.all()

        if not selected_fields:
            serialized = [
                document.model_dump(exclude=exclude, exclude_none=exclude_none)
                for document in documents
            ]
        else:
            serialized = [
                document.model_dump(
                    exclude=exclude, exclude_none=exclude_none, include=selected_fields
                )
                for document in documents
            ]

        if not __as_tuple__:
            return serialized

        if not flatten:
            return [tuple(document.values()) for document in serialized]
        try:
            return [document[selected_fields[0]] for document in serialized]
        except (IndexError, KeyError):
            field_name = selected_fields[0] if selected_fields else ""
            raise FieldDefinitionError(
                detail=f"{field_name} does not exist in the results."
            ) from None

    async def values_list(
        self,
        fields: Union[List[str], str, None] = None,
        exclude: Union[Sequence[str], Set[str], None] = None,
        exclude_none: bool = False,
        flat: bool = False,
    ) -> List[Any]:
        """
        Returns the results in a python dictionary format.
        """

        fields = fields or []
        if flat and len(fields) > 1:
            raise FieldDefinitionError(
                detail=f"Maximum of 1 in fields when `flat` is enables, got {len(fields)} instead."
            ) from None

        if flat and isinstance(fields, str):
            fields = [fields]

        if isinstance(fields, str):
            fields = [fields]

        return await self.values(
            fields=fields,
            exclude=exclude,
            exclude_none=exclude_none,
            flatten=flat,
            __as_tuple__=True,
        )
