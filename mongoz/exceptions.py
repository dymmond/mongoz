from __future__ import annotations

import typing

__all__ = [
    "AbstractDocumentError",
    "DocumentNotFound",
    "FieldDefinitionError",
    "ImproperlyConfigured",
    "IndexError",
    "InvalidKeyError",
    "InvalidObjectIdError",
    "MongozException",
    "MultipleDocumentsReturned",
    "OperatorInvalid",
    "SignalError",
]


class MongozException(Exception):
    """Base class for errors that represent Mongoz-owned semantics."""

    default_message = ""

    def __init__(
        self,
        *args: typing.Any,
        detail: str = "",
    ) -> None:
        self.detail = detail
        fragments = tuple(str(arg) for arg in args)
        if detail:
            fragments += (detail,)
        if not fragments and self.default_message:
            fragments = (self.default_message,)
        super().__init__(*fragments)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)!r})"

    def __str__(self) -> str:
        return " ".join(self.args).strip()


class DocumentNotFound(MongozException):
    default_message = "Document not found."


class MultipleDocumentsReturned(MongozException):
    default_message = "Multiple documents returned."


class FieldDefinitionError(MongozException): ...


class ImproperlyConfigured(MongozException): ...


class InvalidObjectIdError(MongozException): ...


class InvalidKeyError(MongozException): ...


class SignalError(MongozException): ...


class AbstractDocumentError(MongozException): ...


class OperatorInvalid(MongozException): ...


class IndexError(MongozException): ...
