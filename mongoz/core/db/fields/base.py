import decimal
from typing import Any, Callable, ClassVar, Dict, Optional, Pattern, Sequence, Union

from pydantic._internal import _repr
from pydantic.fields import FieldInfo

from mongoz.core.connection.database import Database
from mongoz.core.connection.registry import Registry
from mongoz.types import Undefined

mongoz_setattr = object.__setattr__


class BaseField(FieldInfo, _repr.Representation):
    """
    The base field for all Mongoz data model fields.
    """

    __namespace__: ClassVar[Union[Dict[str, Any], None]] = None

    def __init__(
        self,
        *,
        default: Any = Undefined,
        title: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.max_digits: str = kwargs.pop("max_digits", None)
        self.decimal_places: str = kwargs.pop("decimal_places", None)

        super().__init__(**kwargs)

        self.null: bool = kwargs.pop("null", False)
        if self.null and default is Undefined:
            default = None
        if default is not Undefined:
            self.default = default
        if default is not None:
            self.null = True

        self.defaulf_factory: Optional[Callable[..., Any]] = kwargs.pop(
            "defaulf_factory", Undefined
        )
        self.field_type: Any = kwargs.pop("__type__", None)
        self.__original_type__: type = kwargs.pop("__original_type__", None)
        self.title = title
        self.description = description
        self.read_only: bool = kwargs.pop("read_only", False)
        self.help_text: str = kwargs.pop("help_text", None)
        self.pattern: Pattern = kwargs.pop("pattern", None)
        self.unique: bool = kwargs.pop("unique", False)
        self.index: bool = kwargs.pop("index", False)
        self.choices: Sequence = kwargs.pop("choices", None)
        self.owner: Any = kwargs.pop("owner", None)
        self.name: str = kwargs.pop("name", None)
        self.alias: str = kwargs.pop("alias", None)
        self.min_length: Optional[Union[int, float, decimal.Decimal]] = kwargs.pop(
            "min_length", None
        )
        self.max_length: Optional[Union[int, float, decimal.Decimal]] = kwargs.pop(
            "max_length", None
        )
        self.minimum: Optional[Union[int, float, decimal.Decimal]] = kwargs.pop("minimum", None)
        self.maximum: Optional[Union[int, float, decimal.Decimal]] = kwargs.pop("maximum", None)
        self.multiple_of: Optional[Union[int, float, decimal.Decimal]] = kwargs.pop(
            "multiple_of", None
        )
        self.registry: Registry = kwargs.pop("registry", None)
        self.database: Database = kwargs.pop("database", None)
        self.comment = kwargs.pop("comment", None)

        if self.name and not self.alias:
            self.alias = self.name

        if self.alias and not self.name:
            self.name = self.alias

        for name, value in kwargs.items():
            mongoz_setattr(self, name, value)

        if isinstance(self.default, bool):
            self.null = True
        self.__namespace__ = {k: v for k, v in self.__dict__.items() if k != "__namespace__"}

    @property
    def namespace(self) -> Any:
        """Returns the properties added to the fields in a dict format"""
        return self.__namespace__

    def is_required(self) -> bool:
        """Check if the argument is required.

        Returns:
            `True` if the argument is required, `False` otherwise.
        """
        required = False if self.null else True
        return bool(required)

    def get_alias(self) -> str:
        """
        Used to translate the model column names into database column tables.
        """
        return self.name

    def has_default(self) -> bool:
        """Checks if the field has a default value set"""
        return bool(self.default is not None and self.default is not Undefined)

    def get_default_value(self) -> Any:
        default = getattr(self, "default", None)
        if callable(default):
            return default()
        return default


class MongozField(BaseField):
    ...
