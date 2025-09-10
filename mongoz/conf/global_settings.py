from functools import cached_property
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Dict,
    List,
    cast,
)

from pydantic_settings import BaseSettings, SettingsConfigDict

from mongoz.exceptions import OperatorInvalid

if TYPE_CHECKING:
    from mongoz import Expression


class MongozSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="allow",
        ignored_types=(cached_property,),
        arbitrary_types_allowed=True,
    )

    ipython_args: ClassVar[List[str]] = ["--no-banner"]
    ptpython_config_file: str = "~/.config/ptpython/config.py"

    parsed_ids: ClassVar[List[str]] = ["id", "pk"]

    filter_operators: ClassVar[Dict[str, str]] = {
        "exact": "eq",
        "neq": "neq",
        "contains": "contains",
        "icontains": "icontains",
        "in": "in_",
        "not_in": "not_in",
        "pattern": "pattern",
        "where": "where",
        "gte": "gte",
        "gt": "gt",
        "lt": "lt",
        "lte": "lte",
        "asc": "asc",
        "desc": "desc",
        "not": "not_",
        "startswith": "startswith",
        "istartswith": "istartswith",
        "endswith": "endswith",
        "iendswith": "iendswith",
        "date": "date",
    }

    def get_operator(self, name: str) -> "Expression":
        """
        Returns the operator associated to the given expression passed.
        """
        from mongoz.core.db.querysets.operators import Q

        if name not in self.filter_operators:
            raise OperatorInvalid(f"`{name}` is not a valid operator.")
        return cast("Expression", getattr(Q, self.filter_operators[name]))

    @cached_property
    def operators(self) -> List[str]:
        """
        Returns a list of valid operators.
        """
        return list(self.filter_operators.keys())

    @cached_property
    def stringified_operators(self) -> str:
        """
        Returns a list of valid operators.
        """
        return ", ".join(self.operators)
