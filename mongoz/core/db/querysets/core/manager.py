from __future__ import annotations

from datetime import datetime, timedelta
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Dict,
    Generator,
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
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.command_cursor import AsyncCommandCursor
from typing_extensions import Literal, Self

from mongoz import settings
from mongoz.conf.global_settings import QueryOperator
from mongoz.core.connection.collections import Collection
from mongoz.core.db.datastructures import Order
from mongoz.core.db.fields import base
from mongoz.core.db.querysets.core.constants import (
    GREATNESS_EQUALITY,
    LIST_EQUALITY,
    ORDER_EQUALITY,
    VALUE_EQUALITY,
)
from mongoz.core.db.querysets.core.protocols import (
    AwaitableQuery,
)
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
from mongoz.utils.enums import OrderEnum

if TYPE_CHECKING:
    from pymongo.asynchronous.client_session import AsyncClientSession

    from mongoz.core.db.documents import Document

T = TypeVar("T", bound="Document")


class Manager(SessionBoundQuery, AwaitableQuery[T], Generic[T]):
    def __init__(
        self,
        model_class: Union[Type[T], None] = None,
        filter_by: Union[List[Expression], None] = None,
        sort_by: Union[List[SortExpression], None] = None,
        only_fields: Union[Sequence[str], None] = None,
        defer_fields: Union[Sequence[str], None] = None,
        unwound_fields: Union[Dict[str, Any], None] = None,
        lookups_on: Union[Dict[str, str], None] = None,
        lookup_queries: Union[List[Any], None] = None,
        session: Union["AsyncClientSession", None] = None,
    ) -> None:
        self._model_class = model_class

        model_collection = None if model_class is None else model_class.meta.collection
        if isinstance(model_collection, Collection):
            self.__collection = model_collection._collection
        else:
            self.__collection = None

        self._filter: List[Expression] = [] if filter_by is None else filter_by
        self._limit_count = 0
        self._skip_count = 0
        self._sort: List[SortExpression] = [] if sort_by is None else sort_by
        self._only_fields = [] if only_fields is None else list(only_fields)
        self._defer_fields = [] if defer_fields is None else list(defer_fields)
        self._lookups_on: Union[Dict[str, str], None] = lookups_on
        self._lookup_queries: Union[List[Any], None] = lookup_queries
        self._unwound_fields: Union[Dict[str, Any], None] = unwound_fields
        self.extra: Dict[str, Any] = {}
        self._session = session

    @property
    def model_class(self) -> Type[T]:
        if self._model_class is None:
            raise AttributeError("Manager is not bound to a document class")
        return self._model_class

    @model_class.setter
    def model_class(self, value: Union[Type[T], None]) -> None:
        self._model_class = value

    @property
    def _collection(self) -> AsyncCollection[Dict[str, Any]]:
        if self.__collection is None:
            raise AttributeError("Manager is not bound to a collection")
        return self.__collection

    @_collection.setter
    def _collection(self, value: Union[AsyncCollection[Dict[str, Any]], None]) -> None:
        self.__collection = value

    def __get__(self, instance: object, owner: Type[T]) -> Self:
        return self.__class__(model_class=owner)

    def using(self, database_name: str) -> Self:
        """
        **Type** Public

        **Arguments:**
            - database_name (str): string contains the database name.

        **Returns:**
            - Object: self instance.

        **Raises:**
            - None

        This method is use to select the database:
            - get the data base using the get_database method form the meta \
                class registry using the database_name that provided in \
                    argument.
            - store the database object as database.
            - get the collection from the data base based on \
                self._collection.name
            - return the self instance.
        """
        manager = self.clone()
        if manager.model_class.meta.registry is None:
            raise RuntimeError(f"Document {manager.model_class.__name__} has no registry")
        database = manager.model_class.meta.registry.get_database(database_name)
        manager._collection = database.get_collection(manager._collection.name)._collection
        return manager

    def clone(self) -> Self:
        manager = self.__class__.__new__(self.__class__)
        manager.model_class = self.model_class
        manager._filter = list(self._filter)
        manager._limit_count = self._limit_count
        manager._skip_count = self._skip_count
        manager._sort = list(self._sort)
        manager._collection = self._collection
        manager._only_fields = list(self._only_fields)
        manager._defer_fields = list(self._defer_fields)
        manager._lookups_on = None if self._lookups_on is None else dict(self._lookups_on)
        manager._lookup_queries = (
            None if self._lookup_queries is None else list(self._lookup_queries)
        )
        manager._unwound_fields = (
            None if self._unwound_fields is None else dict(self._unwound_fields)
        )
        manager.extra = dict(self.extra)
        manager._session = self._session
        return manager

    def validate_only_and_defer(self) -> None:
        if self._only_fields and self._defer_fields:
            raise FieldDefinitionError("You cannot use .only() and .defer() at the same time.")

    def get_operator(self, name: str) -> QueryOperator:
        """
        Returns the operator for the given filter.
        """
        return settings.get_operator(name)

    def _find_and_replace_id(self, key: str) -> str:
        """
        Making sure the ID is always parsed as `_id`.
        """
        if key in settings.parsed_ids:
            id_field = self.model_class.__mongoz_fields__.get("id")
            if id_field is None or id_field.pydantic_field.alias is None:
                return "_id"
            return id_field.pydantic_field.alias
        model_field = self.model_class.model_fields.get(key)
        if model_field is not None and model_field.alias is not None:
            return model_field.alias
        return key

    def filter_only_and_defer(self, *fields: str, is_only: bool = False) -> Self:
        """
        Validates if should be defer or only and checks it out
        """
        manager = self.clone()
        manager.validate_only_and_defer()

        document_fields = list(fields)

        id_attribute = manager.model_class.meta.id_attribute
        if not isinstance(id_attribute, str):
            id_attribute = id_attribute.alias or id_attribute.name or "id"
        if id_attribute not in fields and is_only:
            document_fields.insert(0, id_attribute)
        only_or_defer = "_only_fields" if is_only else "_defer_fields"

        setattr(manager, only_or_defer, document_fields)
        return manager

    def _refs_expression(self, lookup_parts: List, operators: Dict) -> List[Any]:
        """
        Check if the lookup_parts contains references to the given operators set.
        Because the LOOKUP_SEP is contained in the default operators names, check
        each prefix of the lookup_parts for a match.
        """
        for n in range(len(lookup_parts)):
            if operators.get(lookup_parts[n]):
                return lookup_parts[0 : n - 1]
        return []

    def _related_collection_name(self, field_name: str) -> str:
        field = self.model_class.meta.fields[field_name]
        related_model = field.refer_to
        if not isinstance(related_model, type):
            raise FieldDefinitionError(f"Field {field_name!r} has no document relation")
        related_meta = getattr(related_model, "meta", None)
        collection = getattr(related_meta, "collection", None)
        collection_name = getattr(collection, "name", None)
        if not isinstance(collection_name, str):
            raise FieldDefinitionError(f"Field {field_name!r} has no related collection")
        return collection_name

    def filter_query(self, exclude: bool = False, **kwargs: Any) -> Self:
        """
        Builds the filter query for the given manager.
        """
        clauses: List[Expression] = []
        filter_clauses = list(self._filter)
        sort_clauses = list(self._sort)
        lookups_on = {} if self._lookups_on is None else dict(self._lookups_on)
        lookup_queries = [] if self._lookup_queries is None else list(self._lookup_queries)
        unwound_fields = {} if self._unwound_fields is None else dict(self._unwound_fields)

        for key, value in kwargs.items():
            key = self._find_and_replace_id(key)
            ref_field = None

            if "." in key:
                parts = key.split(".")
                ref_field = parts[0]
                key = parts[1]

            if "__" in key:
                parts = key.split("__")
                lookup_fields = self._refs_expression(parts, settings.filter_operators)
                lookup_operator = parts[-1]
                field_name = self._find_and_replace_id(parts[-2])
                refrence_field = ""
                for field in lookup_fields:
                    related_collection_name = self._related_collection_name(field)
                    lookup_queries.append(
                        {
                            "$lookup": {
                                "from": related_collection_name,
                                "localField": field,
                                "foreignField": "_id",
                                "as": settings.lookup_prefix + field,
                            }
                        }
                    )
                    unwound_fields[settings.lookup_prefix + field] = {
                        "$unwind": {
                            "path": "$" + settings.lookup_prefix + field,
                            "preserveNullAndEmptyArrays": True,
                        }
                    }

                    lookups_on[related_collection_name] = settings.lookup_prefix + refrence_field
                    refrence_field = field
                if refrence_field and ref_field:
                    ref_field = settings.lookup_prefix + refrence_field + "." + ref_field
                if refrence_field:
                    ref_field = settings.lookup_prefix + refrence_field

                if lookup_operator not in settings.filter_operators:
                    raise OperatorInvalid(
                        f"`{lookup_operator}` is not a valid lookup operator. "
                        f"Valid operators: {settings.stringified_operators}"
                    )

                # For "eq", "neq", "contains", "where", "pattern", "startswith", "endswith", "istartswith", "iendswith"
                if lookup_operator in VALUE_EQUALITY:
                    operator = self.get_operator(lookup_operator)
                    expression = operator(
                        (ref_field + "." + field_name if ref_field else field_name),
                        value,
                    )
                    assert isinstance(expression, Expression)

                # For "in" and "not_in"
                elif lookup_operator in LIST_EQUALITY:
                    if not isinstance(value, (tuple, list)):
                        raise OperatorInvalid(
                            f"Operator `{lookup_operator}` requires a list or tuple, "
                            f"got {type(value).__name__}."
                        )

                    # For tuples, convert to a list
                    if isinstance(value, tuple):
                        value = [*value]

                    operator = self.get_operator(lookup_operator)
                    expression = operator(
                        (ref_field + "." + field_name if ref_field else field_name),
                        value,
                    )
                    assert isinstance(expression, Expression)

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
                    expression = operator(
                        (ref_field + "." + field_name if ref_field else field_name)
                    )
                    assert isinstance(expression, SortExpression)
                    sort_clauses.append(expression)
                    continue

                # For "lt", "lte", "gt", "gte"
                elif lookup_operator in GREATNESS_EQUALITY:
                    operator = self.get_operator(lookup_operator)
                    expression = operator(
                        (ref_field + "." + field_name if ref_field else field_name),
                        value,
                    )
                    assert isinstance(expression, Expression)

                # For "date"
                elif lookup_operator == "date":
                    operator = self.get_operator("gte")
                    from_datetime = datetime.combine(value, datetime.min.time())
                    expression1 = operator(
                        (ref_field + "." + field_name if ref_field else field_name),
                        from_datetime,
                    )
                    assert isinstance(expression1, Expression)
                    clauses.append(expression1)
                    operator = self.get_operator("lt")
                    expression = operator(
                        (ref_field + "." + field_name if ref_field else field_name),
                        from_datetime + timedelta(days=1),
                    )
                    assert isinstance(expression, Expression)

                # Add expression to the clauses
                assert isinstance(expression, Expression)
                clauses.append(expression)

            else:
                operator = self.get_operator("exact")
                expression = operator((ref_field + "." + key if ref_field else key), value)
                assert isinstance(expression, Expression)

                clauses.append(expression)

            if exclude:
                operator = self.get_operator("not")
                negated_clauses: List[Expression] = []
                for clause in clauses:
                    negated_clause = operator(clause.key, clause)
                    assert isinstance(negated_clause, Expression)
                    negated_clauses.append(negated_clause)
                clauses = negated_clauses
                filter_clauses += clauses
            else:
                filter_clauses += clauses

        manager = self.__class__(
            model_class=self.model_class,
            filter_by=filter_clauses,
            sort_by=sort_clauses,
            only_fields=self._only_fields,
            defer_fields=self._defer_fields,
            unwound_fields=unwound_fields,
            lookups_on=lookups_on,
            lookup_queries=lookup_queries,
            session=self._session,
        )
        manager._collection = self._collection
        return manager

    def filter(self, **kwargs: Any) -> Self:
        """
        Filters the queryset based on the given clauses.
        """
        manager = self.clone()
        return manager.filter_query(**kwargs)

    def raw(self, *values: Union[bool, Dict[str, Any], Expression]) -> Self:
        """
        Runs a raw query against the database.
        """
        manager = self.clone()
        for value in values:
            manager._filter.extend(parse_query_argument(value, operation="Raw query"))
        return manager

    def all(self, **kwargs: Any) -> Self:
        """
        Returns the queryset records based on specific filters
        """
        manager = self.clone()
        manager.extra = kwargs
        return manager

    def only(self, *fields: str) -> Self:
        """
        Filters by the only fields.
        """
        manager = self.clone()
        return manager.filter_only_and_defer(*fields, is_only=True)

    def defer(self, *fields: str) -> Self:
        """
        Returns a list of documents with the selected defers fields.
        """
        manager = self.clone()
        return manager.filter_only_and_defer(*fields, is_only=False)

    def limit(self, count: int = 0) -> Self:
        manager = self.clone()
        manager._limit_count = count
        return manager

    def skip(self, count: int = 0) -> Self:
        manager = self.clone()
        manager._skip_count = count
        return manager

    def sort(
        self,
        key: Union[Any, None] = None,
        direction: Union[Order, None] = None,
        **kwargs: Any,
    ) -> Self:
        """Sort by (key, direction) or [(key, direction)]."""
        manager = self.clone()

        if kwargs:
            if len(kwargs) != 1:
                raise FieldDefinitionError(
                    "sort() accepts one keyword field per call; chain sort() calls for "
                    "multiple fields."
                )
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
            if not isinstance(key, SortExpression):
                raise FieldDefinitionError("Invalid sort expression.")
            manager._sort.append(key)
        return manager

    async def none(self) -> Self:
        """
        Returns an empty Manager.
        """
        manager = self.clone()
        manager._filter.append(Expression("$expr", "$eq", [1, 0]))
        return manager

    def _pipeline(self) -> List[Any]:
        """Build the canonical aggregation pipeline for this immutable query state."""
        filter_query = Expression.compile_many(self._filter)
        pipeline: List[Any] = []
        if self._lookup_queries:
            pipeline.extend(self._lookup_queries)
        if filter_query:
            pipeline.append({"$match": filter_query})
        if self._sort:
            pipeline.append({"$sort": {expr.key: expr.direction for expr in self._sort}})
        if self._skip_count:
            pipeline.append({"$skip": self._skip_count})
        if self._limit_count:
            pipeline.append({"$limit": self._limit_count})
        return pipeline

    async def _cursor(self) -> AsyncCommandCursor[Dict[str, Any]]:
        return await self._collection.aggregate(self._pipeline(), **self._driver_options)

    async def __aiter__(self) -> AsyncGenerator[T, None]:
        cursor = await self._cursor()
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

    def __await__(
        self,
    ) -> Generator[Any, None, List[T]]:
        return self.execute().__await__()

    async def _all(self) -> List[T]:
        """
        Returns all the results for a given collection of a document
        """
        manager = self.clone()
        cursor = await manager._cursor()

        # For only fields
        is_only_fields = True if manager._only_fields else False
        is_defer_fields = True if manager._defer_fields else False

        async with closing_cursor(cursor):
            results: List[T] = [
                manager.model_class.from_row(
                    document,
                    is_only_fields=is_only_fields,
                    only_fields=manager._only_fields,
                    is_defer_fields=is_defer_fields,
                    defer_fields=manager._defer_fields,
                    from_collection=manager._collection,
                )
                async for document in cursor
            ]

        return results

    async def count(self, **kwargs: Any) -> int:
        """
        Counts all the documents for a given colletion.
        """
        manager = self.clone()

        filter_query = Expression.compile_many(manager._filter)
        return await manager._collection.count_documents(filter_query, **manager._driver_options)

    async def create(self, **kwargs: Any) -> T:
        """
        Creates a mongo db document.
        """
        manager = self.clone()
        instance = await manager.model_class(**kwargs).create(
            manager._collection, session=manager._session
        )
        return instance

    async def delete(self) -> int:
        """Delete documents matching the criteria."""
        manager = self.clone()
        filter_query = Expression.compile_many(manager._filter)
        result = await manager._collection.delete_many(filter_query, **manager._driver_options)

        return result.deleted_count

    async def first(self) -> Union[T, None]:
        """
        Returns the first document of a matching criteria.
        """
        manager = self.clone()

        objects = await manager.limit(1).all()
        if not objects:
            return None
        return objects[0]

    async def last(self) -> Union[T, None]:
        """Return the last result while retaining at most one raw row."""
        manager = self.clone()
        cursor = await manager._cursor()
        last_document: Union[Dict[str, Any], None] = None
        async with closing_cursor(cursor):
            async for document in cursor:
                last_document = document
        if last_document is None:
            return None
        return manager.model_class.from_row(
            last_document,
            is_only_fields=bool(manager._only_fields),
            only_fields=manager._only_fields,
            is_defer_fields=bool(manager._defer_fields),
            defer_fields=manager._defer_fields,
            from_collection=manager._collection,
        )

    async def get(self, **kwargs: Any) -> T:
        """
        Gets a document.
        """
        manager = self.clone()
        if kwargs:
            return await manager.filter(**kwargs).get()

        objects = await manager.limit(2).all()
        if len(objects) == 0:
            raise DocumentNotFound()
        elif len(objects) == 2:
            raise MultipleDocumentsReturned()
        return objects[0]

    async def get_or_none(self, **kwargs: Any) -> Union[T, None]:
        """
        Gets a document or returns None.
        """
        manager = self.clone()

        if kwargs:
            return await manager.filter(**kwargs).get_or_none()

        objects = await manager.limit(2).all()
        if len(objects) == 0:
            return None
        elif len(objects) > 1:
            raise MultipleDocumentsReturned()
        return objects[0]

    async def get_or_create(self, defaults: Union[Dict[str, Any], None] = None) -> T:
        from mongoz.core.db.documents.persistence import get_or_create_document

        manager = self.clone()
        return await get_or_create_document(
            manager.model_class,
            manager._collection,
            manager._filter,
            defaults or {},
            manager._driver_options,
        )

    async def distinct_values(self, key: str) -> List[Any]:
        """
        Returns a list of distinct values filtered by the key.
        """
        manager = self.clone()
        filter_query = Expression.compile_many(manager._filter)
        values = await manager._collection.find(filter_query, **manager._driver_options).distinct(
            key=key
        )
        return values

    async def where(self, condition: Union[str, Code]) -> List[T]:
        """
        Adds a $where clause to the query.

        E.g.: Movie.objects.where('this.a < (this.b + this.c)')
        """
        if not isinstance(condition, (str, Code)):
            raise OperatorInvalid(
                f"The where clause must be a string or bson.Code; got {type(condition).__name__}."
            )

        manager = self.clone()

        filter_query = Expression.compile_many(manager._filter)
        cursor = manager._collection.find(filter_query, **manager._driver_options).where(condition)
        async with closing_cursor(cursor):
            return [manager.model_class(**document) async for document in cursor]

    async def update(self, **kwargs: Any) -> List[T]:
        """
        Updates a document
        """
        manager = self.clone()
        return await manager.update_many(**kwargs)

    async def update_many(self, **kwargs: Any) -> List[T]:
        """
        Updates many documents (bulk update)
        """
        from mongoz.core.db.documents.persistence import patch_many

        manager = self.clone()
        if not kwargs:
            return await manager._all()
        update, identifiers = await patch_many(
            manager.model_class,
            manager._collection,
            manager._filter,
            kwargs,
            manager._driver_options,
        )
        if not identifiers:
            return []
        manager._filter = [Expression("_id", "$in", identifiers)]
        manager._filter.extend(
            Expression(name, "$eq", value) for name, value in update.storage.items()
        )
        return await manager._all()

    async def create_many(self, models: List[T]) -> List[T]:
        """
        Creates many documents (bulk create).
        """
        manager = self.clone()
        return await manager.model_class.create_many(
            models=models,
            collection=manager._collection,
            session=manager._session,
        )

    async def bulk_create(self, models: List[T]) -> List[T]:
        """
        Bulk creates many documents
        """
        manager = self.clone()
        return await manager.create_many(models=models)

    async def bulk_update(self, **kwargs: Any) -> List[T]:
        manager = self.clone()
        return await manager.update_many(**kwargs)

    async def get_document_by_id(self, id: Union[str, bson.ObjectId]) -> T:
        """
        Gets a document by the id
        """
        manager = self.clone()
        return await manager.model_class.get_document_by_id(id, session=manager._session)

    def _rename_lookup(self, field: str) -> List[str]:
        """
        Split a field string into parts based on "." with "__" meaning lookup rename.
        """
        raw_parts = field.split(".")
        parts = []

        for p in raw_parts:
            if "__" in p:
                sub = p.split("__")
                for i, s in enumerate(sub):
                    if i == 0:
                        parts.append(
                            self.model_class.model_fields[s].refer_to.meta.collection.name
                        )
                    else:
                        parts.append(s)
            else:
                parts.append(p)
        return parts

    def _ensure_list_level(self, node: dict, key: str) -> Dict[str, Any]:
        """
        Ensure that list fields are wrapped under __all__.
        """
        if key not in node:
            node[key] = {"__all__": {}}
            return node[key]["__all__"]

        # key exists
        if node[key] is True:
            node[key] = {"__all__": {}}
            return node[key]["__all__"]

        if "__all__" not in node[key]:
            node[key]["__all__"] = {}

        return node[key]["__all__"]

    def _insert_path(self, include_map: dict, parts: list[str]) -> None:
        """
        Recursive insertion with automatic __all__ for list-like fields.
        Every nested field is assumed to be list-of-dict, unless it's the last key.
        """

        head = parts[0]

        # last part → include True directly
        if len(parts) == 1:
            include_map[head] = True
            return

        # For nested parts → treat as list-of-dict by default
        next_level = self._ensure_list_level(include_map, head)

        self._insert_path(next_level, parts[1:])

    def _build_include_map(self, fields: list[str]) -> Dict[str, Any]:
        """
        Main function to build Pydantic include format.

        Supports:
        - unlimited recursion
        - list-of-dictionaries via "."
        - lookup renaming via "__"
        """
        include: Dict = {}

        for field in fields:
            # Apply lookup renaming ("__")
            parts = self._rename_lookup(field)

            # Process parts recursively
            self._insert_path(include, parts)

        return include

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
        manager = self.clone()
        documents = await manager.all()

        if not selected_fields:
            serialized = [
                document.model_dump(exclude=exclude, exclude_none=exclude_none)
                for document in documents
            ]
        else:
            serialized = [
                document.model_dump(
                    exclude=exclude,
                    exclude_none=exclude_none,
                    include=self._build_include_map(selected_fields),
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
        manager = self.clone()

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

    async def exists(self, **kwargs: Any) -> bool:
        """
        Returns a boolean checking if the record exists.
        """
        manager: "Manager" = self.clone()
        if kwargs:
            result = await manager.filter(**kwargs)
            return bool(len(result) > 0)

        objects = await manager.limit(2).all()
        return bool(len(objects) > 0)

    async def exclude(self, **kwargs: Any) -> List[T]:
        """
        Filters everything and excludes based on a specific condition.
        """
        manager = self.clone()
        return await manager.filter_query(exclude=True, **kwargs)

    async def execute(self) -> List[T]:
        manager = self.clone()
        records = await manager._all(**manager.extra)
        return records
