from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Sequence, Type, TypeVar, Union, cast

from pymongo.asynchronous.collection import AsyncCollection

from mongoz import settings
from mongoz.core.db.documents.base import MongozBaseModel
from mongoz.core.db.documents.metaclasses import MetaInfo

if TYPE_CHECKING:  # pragma: no cover
    from mongoz import Document

T = TypeVar("T", bound="Document")


class DocumentRow(MongozBaseModel):
    """
    Builds a row for a specific document
    """

    @classmethod
    def from_row(
        cls: Type[T],
        row: Dict[str, Any],
        is_only_fields: bool = False,
        is_defer_fields: bool = False,
        only_fields: Union[Sequence[str], None] = None,
        defer_fields: Union[Sequence[str], None] = None,
        from_collection: Union[AsyncCollection, None] = None,
    ) -> T:
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
                    cls.validate_id_field(name)
                    for name in row.keys()
                    if name not in (defer_fields or ())
                ]
            )
            assert mapping is not None

            for column, value in row.items():
                column = cls.validate_id_field(column)

                if column not in mapping:
                    continue

                if column not in item:
                    item[column] = value

            # We need to generify the document fields to make sure we can populate the
            # model without mandatory fields
            model = cast(T, cls.proxy_document(**item))
            model._mongoz_collection = from_collection
            return model
        else:
            for column, value in row.items():
                column = cls.validate_id_field(column)
                if column not in item:
                    if settings.lookup_prefix in column:
                        loopkup_field = column.split(settings.lookup_prefix)[-1]
                        values = []
                        for data in value:
                            if data.get("_id"):
                                data["id"] = data.pop("_id", None)
                            related_model = cls.meta.fields[loopkup_field].refer_to
                            assert isinstance(related_model, type)
                            values.append(related_model(**data))
                        related_model = cls.meta.fields[loopkup_field].refer_to
                        assert isinstance(related_model, type)
                        related_meta = getattr(related_model, "meta", None)
                        assert isinstance(related_meta, MetaInfo)
                        assert related_meta.collection is not None
                        item[related_meta.collection.name] = values
                    else:
                        item[column] = value

        model = cls(**item)
        model._mongoz_collection = from_collection
        return model

    @classmethod
    def validate_id_field(cls, field: str) -> str:
        if field in ["_id", "id", "pk"]:
            field = "id"
        return field
