from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Mapping, Tuple, Type

import bson
import pydantic
from bson.decimal128 import Decimal128
from pydantic import BaseModel, ConfigDict, SerializerFunctionWrapHandler, field_serializer

from mongoz.core.signals.signal import Signal


def _convert_supported_json_values(value: Any) -> tuple[Any, bool]:
    """Convert supported arbitrary values and report whether conversion was required."""
    if isinstance(value, (bson.ObjectId, Signal)):
        return str(value), True
    if isinstance(value, dict):
        converted = {}
        changed = False
        for key, item in value.items():
            converted_item, item_changed = _convert_supported_json_values(item)
            converted[key] = converted_item
            changed = changed or item_changed
        return converted, changed
    if isinstance(value, (list, tuple, set, frozenset)):
        converted_items = [_convert_supported_json_values(item) for item in value]
        return [item for item, _ in converted_items], any(
            changed for _, changed in converted_items
        )
    return value, False


class DescriptiveMeta:
    """
    The `Meta` class used to configure each metadata of the model.
    Abstract classes are not generated in the database, instead, they are simply used as
    a reference for field generation.

    Usage:

    .. code-block:: python3

        class User(Document):
            ...

            class Meta:
                registry = models
                tablename = "users"

    """

    ...  # pragma: no cover


class ModelDump(BaseModel):
    """
    Definition for a model dump. This is used to generate the model fields and their
    respective values.
    """

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    @field_serializer("*", mode="wrap", when_used="json", check_fields=False)
    def serialize_supported_json_values(
        self, value: Any, handler: SerializerFunctionWrapHandler
    ) -> Any:
        """Preserve BSON and signal JSON output while delegating all other serialization."""
        converted, changed = _convert_supported_json_values(value)
        return converted if changed else handler(value)

    def convert_decimal(self, model_dump_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively converts Decimal values in the model_dump_dict to Decimal128.

        Args:
            model_dump_dict (Dict[str, Any]): The dictionary to convert.

        Returns:
            Dict[str, Any]: The converted dictionary.
        """

        if not model_dump_dict:
            return model_dump_dict

        for key, value in model_dump_dict.items():
            if isinstance(value, dict):
                self.convert_decimal(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self.convert_decimal(item)
            elif isinstance(value, Decimal):
                model_dump_dict[key] = Decimal128(str(value))
        return model_dump_dict

    def model_dump(self, show_id: bool = False, **kwargs: Any) -> Dict[str, Any]:
        """
        Args:
            show_pk: bool - Enforces showing the id in the model_dump.
        """
        model = super().model_dump(**kwargs)
        if "id" not in model and show_id:
            model = {**{"id": getattr(self, "id", None)}, **model}
        model_dump = self.convert_decimal(model)
        return model_dump


def create_validation_model(
    name: str, field_definitions: Mapping[str, Tuple[Any, Any]]
) -> Type[ModelDump]:
    """Create the transient Pydantic model used to validate partial updates."""
    # Pydantic's overload cannot express dynamic field definitions until PEP 747.
    return pydantic.create_model(  # ty: ignore[no-matching-overload]
        name,
        __base__=ModelDump,
        **field_definitions,
    )
