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
from mongoz.core.db.querysets.core.constants import (
    GREATNESS_EQUALITY,
    LIST_EQUALITY,
    ORDER_EQUALITY,
    VALUE_EQUALITY,
)
from mongoz.core.db.querysets.expressions import Expression, SortExpression
from mongoz.exceptions import DocumentNotFound, MultipleDumentsReturned
from mongoz.protocols.queryset import QuerySetProtocol
from mongoz.utils.enums import OrderEnum

if TYPE_CHECKING:
    from mongoz.core.db.documents import Document

T = TypeVar("T", bound="Document")


class Manager(QuerySetProtocol, Generic[T]):
    def __init__(
        self,
        model_class: Union[Type["Document"], None] = None,
        filter_by: Union[List[Expression], None] = None,
        sort_by: Union[List[SortExpression], None] = None,
    ) -> None:
        self.model_class = model_class

        if self.model_class:
            self._collection = self.model_class.meta.collection._collection  # type: ignore
        else:
            self._collection = None

        self._filter: List[Expression] = [] if filter_by is None else filter_by
        self._limit_count = 0
        self._skip_count = 0
        self._sort: List[SortExpression] = [] if sort_by is None else sort_by

    def __get__(self, instance: Any, owner: Any) -> "Manager":
        return self.__class__(model_class=owner)

    def clone(self) -> Any:
        manager = self.__class__.__new__(self.__class__)
        manager.model_class = self.model_class
        manager._filter = self._filter
        manager._limit_count = self._limit_count
        manager._skip_count = self._skip_count
        manager._sort = self._sort
        manager._collection = self._collection
        return manager

    def get_operator(self, name: str) -> Expression:
        """
        Returns the operator for the given filter.
        """
        return cast(Expression, settings.get_operator(name))

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

    def _find_and_replace_id(self, key: str) -> str:
        """
        Making sure the ID is always parsed as `_id`.
        """

        if key in settings.parsed_ids:
            return cast(str, self.model_class.id.pydantic_field.alias)  # type: ignore
        return key

    def filter_query(self, exclude: bool = False, **kwargs: Any) -> "Manager":
        """
        Builds the filter query for the given manager.
        """
        clauses = []
        filter_clauses = self._filter
        sort_clauses = self._sort

        for key, value in kwargs.items():
            key = self._find_and_replace_id(key)

            if "__" in key:
                parts = key.split("__")
                lookup_operator = parts[-1]
                field_name = parts[-2]

                assert (
                    lookup_operator in settings.filter_operators
                ), f"`{lookup_operator}` is not a valid lookup operator. Valid operators: {settings.stringified_operators}"

                # For "eq", "neq", "contains", "where", "pattern"
                if lookup_operator in VALUE_EQUALITY:
                    operator = self.get_operator(lookup_operator)
                    expression = operator(field_name, value)  # type: ignore

                # For "in" and "not_in"
                elif lookup_operator in LIST_EQUALITY:
                    assert isinstance(
                        value, (tuple, list)
                    ), f"Using the operator `{lookup_operator}` it requires the value to be a list or a tuple, got {type(value)}"

                    # For tuples, convert to a list
                    if isinstance(value, tuple):
                        value = [*value]

                    operator = self.get_operator(lookup_operator)
                    expression = operator(field_name, value)  # type: ignore

                # For "asc" and "desc"
                elif lookup_operator in ORDER_EQUALITY:
                    asc_or_desc: Union[str, None] = None

                    if (
                        lookup_operator == OrderEnum.ASCENDING
                        and value
                        or lookup_operator == OrderEnum.DESCENDING
                        and value
                    ):
                        asc_or_desc = lookup_operator
                    elif lookup_operator == OrderEnum.ASCENDING and value is False:
                        asc_or_desc = OrderEnum.DESCENDING
                    elif lookup_operator == OrderEnum.DESCENDING and value is False:
                        asc_or_desc = OrderEnum.ASCENDING
                    else:
                        asc_or_desc = OrderEnum.ASCENDING

                    operator = self.get_operator(asc_or_desc)
                    expression = operator(field_name)  # type: ignore
                    sort_clauses.append(expression)
                    continue

                # For "lt", "lte", "gt", "gte"
                elif lookup_operator in GREATNESS_EQUALITY:
                    operator = self.get_operator(lookup_operator)
                    expression = operator(field_name, value)  # type: ignore

                # Add expression to the clauses
                clauses.append(expression)

            else:
                operator = self.get_operator("exact")
                expression = operator(key, value)  # type: ignore
                clauses.append(expression)

            filter_clauses += clauses

        return cast(
            "Manager",
            self.__class__(
                model_class=self.model_class, filter_by=filter_clauses, sort_by=sort_clauses
            ),
        )

    def filter(
        self, clause: Union[str, List[Expression], None] = None, **kwargs: Any
    ) -> "Manager":
        """
        Filters the queryset based on the given clauses.
        """
        manager: "Manager" = self.clone()

        if clause is None:
            return manager.filter_query(**kwargs)
        manager._filter.append(clause)
        return manager

    def raw(self, *values: Union[bool, Dict, Expression]) -> "Manager":
        """
        Runs a raw query against the database.
        """
        manager: "Manager" = self.clone()
        for value in values:
            assert isinstance(value, (dict, Expression)), "Invalid argument to Raw"
            if isinstance(value, dict):
                query_expressions = Expression.unpack(value)
                manager._filter.extend(query_expressions)
            else:
                manager._filter.append(value)
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
        return cast(T, objects[0])

    async def last(self) -> Union[T, None]:
        """
        Returns the last document of a matching criteria.
        """
        manager: "Manager" = self.clone()
        objects = await manager.all()
        if not objects:
            return None
        return cast(T, objects[-1])

    async def get(self, **kwargs: Any) -> Union["T", "Document"]:
        """
        Gets a document.
        """
        manager: "Manager" = self.clone()

        if kwargs:
            return await manager.filter(**kwargs).get()

        objects = await manager.limit(2).all()
        if len(objects) == 0:
            raise DocumentNotFound()
        elif len(objects) == 2:
            raise MultipleDumentsReturned()
        return cast(T, objects[0])

    async def get_or_none(self, **kwargs: Any) -> Union["T", "Document", None]:
        """
        Gets a document or returns None.
        """
        manager: "Manager" = self.clone()

        if kwargs:
            return await manager.filter(**kwargs).get_or_none()

        objects = await manager.limit(2).all()
        if len(objects) == 0:
            return None
        elif len(objects) > 1:
            raise MultipleDumentsReturned()
        return cast(T, objects[0])

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
        return cast(T, manager.model_class(**model))

    async def distinct_values(self, key: str) -> List[Any]:
        """
        Returns a list of distinct values filtered by the key.
        """
        manager: "Manager" = self.clone()
        filter_query = Expression.compile_many(manager._filter)
        values = await manager._collection.find(filter_query).distinct(key=key)
        return cast(List[Any], values)

    def exclude(self, **kwargs: Any) -> "Manager":
        """
        Filters everything and excludes based on a specific field.
        """
        manager: "Manager" = self.clone()
        return manager.filter_query(exclude=True, **kwargs)

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

    def sort(
        self, key: Union[Any, None] = None, direction: Union[Order, None] = None, **kwargs: Any
    ) -> "Manager[T]":
        """Sort by (key, direction) or [(key, direction)]."""
        manager: "Manager" = self.clone()

        if kwargs:
            assert (
                len(kwargs) == 1
            ), "`sort` only allows one field per sort. Use `sort(field).sort(field) for multiple fields instead"
            return manager.filter_query(**kwargs)

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
                __model_name=manager.model_class.__name__,  # type: ignore
                __config__=manager.model_class.model_config,  # type: ignore
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
        return await manager.model_class.create_many(models=models)  # type: ignore

    async def get_document_by_id(self, id: Union[str, bson.ObjectId]) -> "Document":
        """
        Gets a document by the id
        """
        manager: "Manager" = self.clone()
        return await manager.model_class.get_document_by_id(id)  # type: ignore

    def __await__(
        self,
    ) -> Generator[Any, None, List["Document"]]:
        return self.all().__await__()  # type: ignore
