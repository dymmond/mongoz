from typing import TYPE_CHECKING, Any, Dict, List, Protocol, Tuple, TypeVar, Union, overload

if TYPE_CHECKING:
    from mongoz.core.db.datastructures import Order
    from mongoz.core.db.documents import Document
    from mongoz.core.db.querysets.base import QuerySet
    from mongoz.core.db.querysets.expressions import SortExpression


T = TypeVar("T", bound="Document")


class QuerySetProtocol(Protocol):
    async def all(self) -> List[T]: ...

    async def count(self) -> int: ...

    async def delete(self) -> int: ...

    async def first(self) -> Union[T, None]: ...

    async def last(self) -> Union[T, None]: ...

    async def get(self) -> T: ...

    async def get_or_create(self, defaults: Union[Dict[str, Any], None]) -> T: ...

    async def limit(self, count: int = 0) -> "QuerySet[T]":  # pragma: no cover
        ...

    async def skip(self, count: int = 0) -> "QuerySet[T]":  # pragma: no cover
        ...

    @overload
    def sort(self, key: "SortExpression") -> "QuerySet[T]":  # pragma: no cover
        ...

    @overload
    def sort(self, key: Any, direction: "Order") -> "QuerySet[T]":  # pragma: no cover
        ...

    @overload
    def sort(self, key: List[Tuple[Any, "Order"]]) -> "QuerySet[T]":  # pragma: no cover
        ...

    def sort(self, key: Any, direction: Union["Order", None] = None) -> "QuerySet[T]": ...

    async def update_many(self, **kwargs: Any) -> List[T]: ...
