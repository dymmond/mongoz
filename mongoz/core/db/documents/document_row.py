from typing import TYPE_CHECKING, Any, Dict, Sequence, Type, Union, cast

from mongoz.core.db.documents.base import MongozBaseModel

if TYPE_CHECKING:  # pragma: no cover
    from mongoz import Document


class DocumentRow(MongozBaseModel):
    """
    Builds a row for a specific document
    """

    @classmethod
    def from_row(
        cls: "Document",
        row: Dict[str, Any],
        is_only_fields: bool = False,
        only_fields: Union[Sequence[str], None] = None,
    ) -> Union[Type["Document"], None]:
        """
        Class method to convert a dictionary row result into a Document row type.
        :return: Document class.
        """
        item: Dict[str, Any] = {}

        for column, value in row.items():
            if column not in item:
                item[column] = value

        model = cast("Type[Document]", cls(**item))  # type: ignore
        return model
