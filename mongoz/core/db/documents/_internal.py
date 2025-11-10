from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

import bson
from bson.decimal128 import Decimal128
from pydantic import BaseModel, ConfigDict

from mongoz.core.signals.signal import Signal


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
        json_encoders={bson.ObjectId: str, Signal: str},
        validate_assignment=True,
    )

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
            model = {**{"id": self.id}, **model}
        model_dump = self.convert_decimal(model)
        return model_dump
