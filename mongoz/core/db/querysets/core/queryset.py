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
    cast,
)

import bson
import pydantic
from bson import Code

from mongoz.core.db.datastructures import Order
from mongoz.core.db.fields import base
from mongoz.core.db.querysets.expressions import Expression, SortExpression
from mongoz.exceptions import DocumentNotFound, FieldDefinitionError, MultipleDocumentsReturned
from mongoz.protocols.queryset import QuerySetProtocol

if TYPE_CHECKING:
    from mongoz.core.db.documents import Document

T = TypeVar("T", bound="Document")


class BaseQuerySet(QuerySetProtocol, Generic[T]):
    def __init__(
        self,
        model_class: Type[T],
        filter_by: List[Expression] = None,
        only_fields: Union[str, None] = None,
        defer_fields: Union[str, None] = None,
    ) -> None:
        self.model_class = model_class
        self._collection = model_class.meta.collection._collection  # type: ignore
        self._filter: List[Expression] = filter_by or []
        self._limit_count = 0
        self._skip_count = 0
        self._sort: List[SortExpression] = []
        self._only_fields = [] if only_fields is None else only_fields
        self._defer_fields = [] if defer_fields is None else defer_fields

    def validate_only_and_defer(self) -> None:
        if self._only_fields and self._defer_fields:
            raise FieldDefinitionError("You cannot use .only() and .defer() at the same time.")

    def filter_only_and_defer(
        self, *fields: Sequence[str], is_only: bool = False
    ) -> "BaseQuerySet[T]":
        """
        Filters by the only fields.
        """
        self.validate_only_and_defer()

        document_fields: List[str] = list(fields)
        if any(not isinstance(name, str) for name in document_fields):
            raise FieldDefinitionError("The fields must be must strings.")

        if self.model_class.meta.id_attribute not in fields and is_only:
            document_fields.insert(0, self.model_class.meta.id_attribute)
        only_or_defer = "_only_fields" if is_only else "_defer_fields"

        setattr(self, only_or_defer, document_fields)
        return self

    def limit(self, count: int = 0) -> "BaseQuerySet[T]":
        self._limit_count = count
        return self

    def skip(self, count: int = 0) -> "BaseQuerySet[T]":
        self._skip_count = count
        return self

    def only(self, *fields: Sequence[str]) -> "BaseQuerySet[T]":
        """
        Filters by the only fields.
        """
        return self.filter_only_and_defer(*fields, is_only=True)

    def defer(self, *fields: Sequence[str]) -> "BaseQuerySet[T]":
        """
        Returns a list of documents with the selected defers fields.
        """
        return self.filter_only_and_defer(*fields, is_only=False)

    def sort(self, key: Any, direction: Union[Order, None] = None) -> "BaseQuerySet[T]":
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

    def query(self, *args: Union[bool, Dict, Expression]) -> "BaseQuerySet[T]":
        for arg in args:
            assert isinstance(arg, (dict, Expression)), "Invalid argument to Query"
            if isinstance(arg, dict):
                query_expressions = Expression.unpack(arg)
                self._filter.extend(query_expressions)
            else:
                self._filter.append(arg)
        return self


class QuerySet(BaseQuerySet[T]):
    async def __aiter__(self) -> AsyncGenerator[T, None]:
        filter_query = Expression.compile_many(self._filter)
        cursor = self._collection.find(filter_query)

        async for document in cursor:
            yield self.model_class(**document)

    async def none(self) -> "QuerySet[T]":
        """
        Returns an empty QuerySet
        """
        return self.__class__(model_class=self.model_class)

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

        # For only fields
        is_only_fields = True if self._only_fields else False
        is_defer_fields = True if self._defer_fields else False

        results: List[T] = [
            self.model_class.from_row(  # type: ignore
                document,
                is_only_fields=is_only_fields,
                only_fields=self._only_fields,
                is_defer_fields=is_defer_fields,
                defer_fields=self._defer_fields,
            )
            async for document in cursor
        ]

        return results

    async def count(self) -> int:
        """
        Counts all the documents for a given colletion.
        """

        filter_query = Expression.compile_many(self._filter)
        return cast(int, await self._collection.count_documents(filter_query))

    async def delete(self) -> int:
        """Delete documents matching the criteria."""
        filter_query = Expression.compile_many(self._filter)
        result = await self._collection.delete_many(filter_query)

        return cast(int, result.deleted_count)

    async def first(self) -> Union[T, None]:
        """
        Returns the first document of a matching criteria.
        """

        objects: List[T] = await self.limit(1).all()
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
        objects: List[T] = await self.limit(2).all()
        if len(objects) == 0:
            raise DocumentNotFound()
        elif len(objects) == 2:
            raise MultipleDocumentsReturned()
        return objects[0]

    async def get_or_none(self) -> Union["T", "Document", None]:
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

        E.g.: Movie.query().where('this.a < (this.b + this.c)')
        """
        assert isinstance(
            condition, (str, Code)
        ), "The where clause must be a string or a bson.Code"

        filter_query = Expression.compile_many(self._filter)
        cursor = self._collection.find(filter_query).where(condition)
        return [self.model_class(**document) async for document in cursor]

    async def bulk_create(self, models: List["Document"]) -> List["Document"]:
        """
        Creates many documents (bulk create).
        """
        return await self.model_class.create_many(models=models)

    async def update(self, **kwargs: Any) -> List[T]:
        """
        Updates a document
        """
        return await self.update_many(**kwargs)

    async def bulk_update(self, **kwargs: Any) -> List[T]:
        return await self.update_many(**kwargs)

    async def update_many(self, **kwargs: Any) -> List[T]:
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

    async def get_document_by_id(self, id: Union[str, bson.ObjectId]) -> "Document":
        """
        Gets a document by the id.
        """
        return await self.model_class.get_document_by_id(id)

    async def values(
        self,
        fields: Union[Sequence[str], str, None] = None,
        exclude: Union[Sequence[str], Set[str]] = None,
        exclude_none: bool = False,
        flatten: bool = False,
        **kwargs: Any,
    ) -> List[T]:
        """
        Returns the results in a python dictionary format.
        """
        fields = fields or []
        documents: List[T] = await self.all()

        if not isinstance(fields, list):
            raise FieldDefinitionError(detail="Fields must be an iterable.")

        if not fields:
            documents = [document.model_dump(exclude=exclude, exclude_none=exclude_none) for document in documents]  # type: ignore
        else:
            documents = [
                document.model_dump(exclude=exclude, exclude_none=exclude_none, include=fields)  # type: ignore
                for document in documents
            ]

        as_tuple = kwargs.pop("__as_tuple__", False)

        if not as_tuple:
            return documents

        if not flatten:
            documents = [tuple(document.values()) for document in documents]  # type: ignore
        else:
            try:
                documents = [document[fields[0]] for document in documents]  # type: ignore
            except KeyError:
                raise FieldDefinitionError(
                    detail=f"{fields[0]} does not exist in the results."
                ) from None
        return documents

    async def values_list(
        self,
        fields: Union[Sequence[str], str, None] = None,
        exclude: Union[Sequence[str], Set[str]] = None,
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
