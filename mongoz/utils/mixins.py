from typing import TYPE_CHECKING, Type, TypeVar

from mongoz.exceptions import AbstractDocumentError

if TYPE_CHECKING:
    from mongoz import Document

T = TypeVar("T", bound="Document")


def is_operation_allowed(self: Type["Document"]) -> bool:
    if self.meta.abstract:
        raise AbstractDocumentError(
            f"{str(self)} is an abstract class. This operation is not allowed"
        )
    return bool(self.meta.abstract is not None and self.meta.abstract is not False)
