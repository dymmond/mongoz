from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Dict,
    Generator,
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

from mongoz import settings
from mongoz.core.db.datastructures import Order
from mongoz.core.db.fields import base
from mongoz.core.db.querysets.core.constants import (
    GREATNESS_EQUALITY,
    LIST_EQUALITY,
    ORDER_EQUALITY,
    VALUE_EQUALITY,
)
from mongoz.core.db.querysets.core.protocols import AwaitableQuery, MongozDocument
from mongoz.core.db.querysets.expressions import Expression, SortExpression
from mongoz.exceptions import DocumentNotFound, FieldDefinitionError, MultipleDocumentsReturned
from mongoz.protocols.queryset import QuerySetProtocol
from mongoz.utils.enums import OrderEnum

if TYPE_CHECKING:
    from mongoz.core.db.documents import Document

T = TypeVar("T", bound="Document")


class Manager(QuerySetProtocol, AwaitableQuery[MongozDocument]):
    def __init__(
        self,
        model_class: Union[Type["Document"], None] = None,
        filter_by: Union[List[Expression], None] = None,
        sort_by: Union[List[SortExpression], None] = None,
        only_fields: Union[str, None] = None,
        defer_fields: Union[str, None] = None,
    ) -> None:
        self.model_class = model_class  # type: ignore

        if self.model_class:
            self._collection = self.model_class.meta.collection._collection  # type: ignore
        else:
            self._collection = None

        self._filter: List[Expression] = [] if filter_by is None else filter_by
        self._limit_count = 0
        self._skip_count = 0
        self._sort: List[SortExpression] = [] if sort_by is None else sort_by
        self._only_fields = [] if only_fields is None else only_fields
        self._defer_fields = [] if defer_fields is None else defer_fields
        self.extra: Dict[str, Any] = {}

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
        manager._only_fields = self._only_fields
        manager._defer_fields = self._defer_fields
        manager.extra = self.extra
        return manager

    def validate_only_and_defer(self) -> None:
        if self._only_fields and self._defer_fields:
            raise FieldDefinitionError("You cannot use .only() and .defer() at the same time.")

    def get_operator(self, name: str) -> Expression:
        """
        Returns the operator for the given filter.
        """
        return settings.get_operator(name)  # type: ignore

    def _find_and_replace_id(self, key: str) -> str:
        """
        Making sure the ID is always parsed as `_id`.
        """
        if key in settings.parsed_ids:
            return cast(str, self.model_class.id.pydantic_field.alias)  # type: ignore
        return key

    def filter_only_and_defer(self, *fields: Sequence[str], is_only: bool = False) -> "Manager":
        """
        Validates if should be defer or only and checks it out
        """
        manager: "Manager" = self.clone()
        manager.validate_only_and_defer()

        document_fields: List[str] = list(fields)
        if any(not isinstance(name, str) for name in document_fields):
            raise FieldDefinitionError("The fields must be must strings.")

        if manager.model_class.meta.id_attribute not in fields and is_only:
            document_fields.insert(0, manager.model_class.meta.id_attribute)
        only_or_defer = "_only_fields" if is_only else "_defer_fields"

        setattr(manager, only_or_defer, document_fields)
        return manager

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

            if exclude:
                operator = self.get_operator("not")
                clauses = [operator(clause.key, clause) for clause in clauses]  # type: ignore
                filter_clauses += clauses
            else:
                filter_clauses += clauses

        return cast(
            "Manager",
            self.__class__(
                model_class=self.model_class,
                filter_by=filter_clauses,
                sort_by=sort_clauses,
                only_fields=self._only_fields,
                defer_fields=self._defer_fields,
            ),
        )

    def filter(self, **kwargs: Any) -> "Manager":
        """
        Filters the queryset based on the given clauses.
        """
        manager: "Manager" = self.clone()
        return manager.filter_query(**kwargs)

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

    def all(self, **kwargs: Any) -> "Manager":
        """
        Returns the queryset records based on specific filters
        """
        manager: "Manager" = self.clone()
        manager.extra = kwargs
        return manager

    def only(self, *fields: Sequence[str]) -> "Manager":
        """
        Filters by the only fields.
        """
        manager: "Manager" = self.clone()
        return manager.filter_only_and_defer(*fields, is_only=True)

    def defer(self, *fields: Sequence[str]) -> "Manager":
        """
        Returns a list of documents with the selected defers fields.
        """
        manager: "Manager" = self.clone()
        return manager.filter_only_and_defer(*fields, is_only=False)

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

    async def none(self) -> "Manager":
        """
        Returns an empty Manager.
        """
        manager = self.__class__(model_class=self.model_class)
        manager._collection = self.model_class.meta.collection._collection  # type: ignore
        return manager

    async def __aiter__(self) -> AsyncGenerator[T, None]:
        filter_query = Expression.compile_many(self._filter)
        cursor = self._collection.find(filter_query)

        async for document in cursor:
            yield self.model_class(**document)

    def __await__(
        self,
    ) -> Generator[Any, None, List["Document"]]:
        return self.execute().__await__()

    async def _all(self) -> List[T]:
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

        # For only fields
        is_only_fields = True if manager._only_fields else False
        is_defer_fields = True if manager._defer_fields else False

        results: List[T] = [
            manager.model_class.from_row(
                document,
                is_only_fields=is_only_fields,
                only_fields=manager._only_fields,
                is_defer_fields=is_defer_fields,
                defer_fields=manager._defer_fields,
            )
            async for document in cursor
        ]

        return results

    async def count(self, **kwargs: Any) -> int:
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
        return cast("Document", instance)

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
        objects: Any = await manager._all()
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
            raise MultipleDocumentsReturned()
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
            raise MultipleDocumentsReturned()
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

    async def update(self, **kwargs: Any) -> List["Document"]:
        """
        Updates a document
        """
        manager: "Manager" = self.clone()
        return await manager.update_many(**kwargs)

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
        return await manager._all()

    async def create_many(self, models: List["Document"]) -> List["Document"]:
        """
        Creates many documents (bulk create).
        """
        manager: "Manager" = self.clone()
        return await manager.model_class.create_many(models=models)  # type: ignore

    async def bulk_create(self, models: List["Document"]) -> List["Document"]:
        """
        Bulk creates many documents
        """
        manager: "Manager" = self.clone()
        return await manager.create_many(models=models)

    async def bulk_update(self, **kwargs: Any) -> List[T]:
        manager: "Manager" = self.clone()
        return await manager.update_many(**kwargs)

    async def get_document_by_id(self, id: Union[str, bson.ObjectId]) -> "Document":
        """
        Gets a document by the id
        """
        manager: "Manager" = self.clone()
        return await manager.model_class.get_document_by_id(id)  # type: ignore

    async def values(
        self,
        fields: Union[Sequence[str], str, None] = None,
        exclude: Union[Sequence[str], Set[str]] = None,
        exclude_none: bool = False,
        flatten: bool = False,
        **kwargs: Any,
    ) -> List["Document"]:
        """
        Returns the results in a python dictionary format.
        """
        fields = fields or []
        manager: "Manager" = self.clone()
        documents: List["Document"] = await manager.all()

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
        manager: "Manager" = self.clone()

        fields = fields or []
        if flat and len(fields) > 1:
            raise FieldDefinitionError(
                detail=f"Maximum of 1 in fields when `flat` is enables, got {len(fields)} instead."
            ) from None

        if flat and isinstance(fields, str):
            fields = [fields]

        if isinstance(fields, str):
            fields = [fields]

        return await manager.values(
            fields=fields,
            exclude=exclude,
            exclude_none=exclude_none,
            flatten=flat,
            __as_tuple__=True,
        )

    async def exclude(self, **kwargs: Any) -> List["Document"]:
        """
        Filters everything and excludes based on a specific condition.
        """
        manager: "Manager" = self.clone()
        return await manager.filter_query(exclude=True, **kwargs)

    async def execute(self) -> Any:
        manager: "Manager" = self.clone()
        records: Any = await manager._all(**manager.extra)
        return records
