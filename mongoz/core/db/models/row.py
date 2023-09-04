import asyncio
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Type, Union, cast

from mongoz.core.db.models.base import MongozBaseModel

if TYPE_CHECKING:  # pragma: no cover
    from mongoz.core.db.models import Model


class ModelRow(MongozBaseModel):
    """
    Builds a row for a specific model
    """

    @classmethod
    def from_row(cls, **kwargs: Any) -> Optional[Type["Model"]]:
        """
        Class method to convert a SQLAlchemy Row result into a EdgyModel row type.

        Looping through select_related fields if the query comes from a select_related operation.
        Validates if exists the select_related and related_field inside the models.

        When select_related and related_field exist for the same field being validated, the related
        field is ignored as it won't override the value already collected from the select_related.

        If there is no select_related, then goes through the related field where it **should**
        only return the instance of the the ForeignKey with the ID, making it lazy loaded.

        :return: Model class.
        """
        ...
