from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from typing_extensions import Self

if TYPE_CHECKING:
    from pymongo.asynchronous.client_session import AsyncClientSession


class SessionBoundQuery:
    """Own immutable PyMongo session binding for Mongoz query objects."""

    _session: AsyncClientSession | None

    def clone(self) -> Self:
        raise NotImplementedError

    @property
    def _driver_options(self) -> Dict[str, Any]:
        return {} if self._session is None else {"session": self._session}

    def using_session(self, session: AsyncClientSession) -> Self:
        """Bind a PyMongo session to a derived query without mutating its parent."""
        query = self.clone()
        query._session = session
        return query
