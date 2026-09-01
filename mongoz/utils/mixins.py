from __future__ import annotations

from typing import TYPE_CHECKING, Type, Union

from mongoz.exceptions import AbstractDocumentError

if TYPE_CHECKING:
    from mongoz import Document


def is_operation_allowed(document: Union[Type["Document"], "Document"]) -> bool:
    if document.meta.abstract:
        raise AbstractDocumentError(
            f"{str(document)} is an abstract class. This operation is not allowed"
        )
    return bool(document.meta.abstract is not None and document.meta.abstract is not False)
