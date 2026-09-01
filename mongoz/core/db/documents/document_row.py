from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Sequence, Type, TypeVar, Union

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
        lookup_fields: Sequence[str] = (),
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

            # Projection results intentionally omit required fields. Constructing the concrete
            # class without validation preserves that partial shape and keeps the runtime type
            # aligned with the public generic return contract.
            model = cls.model_construct(_fields_set=set(item), **item)
            for field_name in cls.model_fields:
                if field_name not in item:
                    model.__dict__.pop(field_name, None)
            model._mongoz_collection = from_collection
            return model
        elif not any(column in lookup_fields for column in row):
            for column, value in row.items():
                column = cls.validate_id_field(column)
                if column not in item:
                    item[column] = value
        else:
            for column, value in row.items():
                source_column = column
                column = cls.validate_id_field(source_column)
                if column not in item:
                    if source_column in lookup_fields:
                        loopkup_field = source_column.removeprefix(settings.lookup_prefix)
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
