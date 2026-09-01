from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import Self

if TYPE_CHECKING:
    from pymongo.asynchronous.client_session import AsyncClientSession

    from mongoz.core.db.datastructures import Order
    from mongoz.core.db.documents import Document
    from mongoz.core.db.querysets.expressions import Expression, SortExpression


T = TypeVar("T", bound="Document")


class QuerySetProtocol(Protocol, Generic[T]):
    def using_session(self, session: "AsyncClientSession") -> Self: ...

    async def all(self) -> List[T]: ...

    async def count(self) -> int: ...

    async def delete(self) -> int: ...

    async def first(self) -> Union[T, None]: ...

    async def last(self) -> Union[T, None]: ...

    async def get(self) -> T: ...

    async def get_or_none(self) -> Union[T, None]: ...

    async def get_or_create(self, defaults: Union[Dict[str, Any], None] = None) -> T: ...

    async def none(self) -> Self: ...

    def limit(self, count: int = 0) -> Self:  # pragma: no cover
        ...

    def skip(self, count: int = 0) -> Self:  # pragma: no cover
        ...

    def only(self, *fields: str) -> Self: ...

    def defer(self, *fields: str) -> Self: ...

    def query(self, *args: Union[bool, Dict[str, Any], "Expression"]) -> Self: ...

    @overload
    def sort(self, key: "SortExpression") -> Self:  # pragma: no cover
        ...

    @overload
    def sort(self, key: Any, direction: "Order") -> Self:  # pragma: no cover
        ...

    @overload
    def sort(self, key: List[Tuple[Any, "Order"]]) -> Self:  # pragma: no cover
        ...

    def sort(self, key: Any, direction: Union["Order", None] = None) -> Self: ...

    async def update_many(self, **kwargs: Any) -> List[T]: ...
