from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Sequence, Type, Union, cast

from motor.motor_asyncio import AsyncIOMotorCollection

from mongoz import settings
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
        is_defer_fields: bool = False,
        only_fields: Union[Sequence[str], None] = None,
        defer_fields: Union[Sequence[str], None] = None,
        from_collection: Union[AsyncIOMotorCollection, None] = None,
    ) -> Union[Type["Document"], None]:
        """
        Class method to convert a dictionary row result into a Document row type.
        :return: Document class.
        """
        item: Dict[str, Any] = {}

        if is_only_fields or is_defer_fields:
            mapping = (
                only_fields
                if is_only_fields
                else [
                    cls.validate_id_field(name) for name in row.keys() if name not in defer_fields  # type: ignore
                ]
            )

            for column, value in row.items():
                column = cls.validate_id_field(column)

                if column not in mapping:  # type: ignore
                    continue

                if column not in item:
                    item[column] = value

            # We need to generify the document fields to make sure we can populate the
            # model without mandatory fields
            model = cast("Type[Document]", cls.proxy_document(**item))
            return model
        else:
            for column, value in row.items():
                column = cls.validate_id_field(column)
                if column not in item:
                    if settings.lookup_prefix in column:
                        loopkup_field = column.split(settings.lookup_prefix)[
                            -1
                        ]
                        values = []
                        for data in value:
                            if data.get("_id"):
                                data["id"] = data.pop("_id", None)
                            values.append(
                                cls.model_fields[loopkup_field].refer_to(
                                    **data
                                )
                            )
                        item[
                            cls.model_fields[
                                loopkup_field
                            ].refer_to.meta.collection.name
                        ] = values
                    else:
                        item[column] = value

        model = cast("Type[Document]", cls(**item))  # type: ignore
        model.Meta.from_collection = from_collection
        return model

    @classmethod
    def validate_id_field(cls, field: str) -> str:
        if field in ["_id", "id", "pk"]:
            field = "id"
        return field
