from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Dict

from typing_extensions import Self

from mongoz.exceptions import FieldDefinitionError

if TYPE_CHECKING:
    from pymongo.asynchronous.client_session import AsyncClientSession


def normalize_projection_fields(fields: Sequence[str] | str | None) -> list[str]:
    """Normalize projection state without treating one field name as characters."""
    if fields is None:
        return []
    normalized = [fields] if isinstance(fields, str) else list(fields)
    if not all(isinstance(field, str) for field in normalized):
        raise FieldDefinitionError("only/defer fields must be strings")
    return normalized


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
