from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, TypeVar

if TYPE_CHECKING:
    from pymongo.asynchronous.client_session import AsyncClientSession

QueryT = TypeVar("QueryT", bound="SessionBoundQuery")


class SessionBoundQuery:
    """Own immutable PyMongo session binding for Mongoz query objects."""

    _session: AsyncClientSession | None

    def clone(self: QueryT) -> QueryT:
        raise NotImplementedError

    @property
    def _driver_options(self) -> Dict[str, Any]:
        return {} if self._session is None else {"session": self._session}

    def using_session(self: QueryT, session: AsyncClientSession) -> QueryT:
        """Bind a PyMongo session to a derived query without mutating its parent."""
        query = self.clone()
        query._session = session
        return query
