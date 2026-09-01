from __future__ import annotations

import decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Optional,
    Pattern,
    Sequence,
    Type,
    Union,
)

from pydantic._internal import _repr
from pydantic.fields import FieldInfo

from mongoz.core.connection.database import Database
from mongoz.core.connection.registry import Registry
from mongoz.core.db.querysets.expressions import Expression
from mongoz.exceptions import InvalidKeyError
from mongoz.types import Undefined

if TYPE_CHECKING:
    from mongoz import Document, EmbeddedDocument

mongoz_setattr = object.__setattr__


# Pydantic marks FieldInfo final for typing, but Mongoz's established runtime field API subclasses it.
class BaseField(FieldInfo, _repr.Representation):  # ty: ignore[subclass-of-final-class]
    """
    The base field for all Mongoz data model fields.
    """

    __namespace__: Optional[Dict[str, Any]] = None

    def __init__(
        self,
        *,
        default: Any = Undefined,
        title: Optional[str] = None,
        description: Optional[str] = None,
        parent: Union[Type["FieldInfo"], None] = None,
        model_class: Union[Type["Document"], Type["EmbeddedDocument"], None] = None,
        **kwargs: Any,
    ) -> None:
        self.max_digits: Optional[int] = kwargs.pop("max_digits", None)
        self.decimal_places: Optional[int] = kwargs.pop("decimal_places", None)

        super().__init__(**kwargs)

        self.null: bool = kwargs.pop("null", False)
        if self.null and default is Undefined:
            default = None
        if default is not Undefined:
            self.default = default
        if default is not None:
            self.null = True

        self.parent = parent
        self.model_class = model_class
        self.refer_to: Union[str, Type["Document"], Type["EmbeddedDocument"], None] = kwargs.pop(
            "refer_to", None
        )
        self.defaulf_factory: Optional[Callable[..., Any]] = kwargs.pop(
            "defaulf_factory", Undefined
        )
        self.field_type: Any = kwargs.pop("__type__", None)
        self.__original_type__: Optional[type] = kwargs.pop("__original_type__", None)
        self.title = title
        self.description = description
        self.read_only: bool = kwargs.pop("read_only", False)
        self.help_text: Optional[str] = kwargs.pop("help_text", None)
        self.pattern: Optional[Pattern[str]] = kwargs.pop("pattern", None)
        self.unique: bool = kwargs.pop("unique", False)
        self.index: bool = kwargs.pop("index", False)
        self.choices: Optional[Sequence[Any]] = kwargs.pop("choices", None)
        self.owner: Any = kwargs.pop("owner", None)
        self.name: Optional[str] = kwargs.pop("name", None)
        self.alias: Optional[str] = kwargs.pop("alias", None)
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
        self.registry: Optional[Registry] = kwargs.pop("registry", None)
        self.database: Optional[Database] = kwargs.pop("database", None)
        self.comment = kwargs.pop("comment", None)
        self.parent = kwargs.pop("parent", None)
        self.sparse = kwargs.pop("sparse", False)

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

    def has_default(self) -> bool:
        return bool(self.default is not None and self.default is not Undefined)

    def get_default_value(self) -> Any:
        default = getattr(self, "default", None)
        if callable(default):
            return default()
        return default

    def validate_field_value(self, value: Any) -> Any:
        return value


class MongozField:
    def __init__(
        self,
        pydantic_field: "FieldInfo",
        parent: Optional["MongozField"] = None,
        model_class: Union[Type["Document"], Type["EmbeddedDocument"], None] = None,
    ) -> None:
        self.model_class = model_class
        self.parent = parent
        self.pydantic_field = pydantic_field

    @property
    def _name(self) -> str:
        alias = self.pydantic_field.alias
        assert alias is not None
        if self.parent:
            return self.parent._name + "." + alias
        return alias

    def __lt__(self, other: Any) -> Expression:
        return Expression(self._name, "$lt", other)

    def __le__(self, other: Any) -> Expression:
        return Expression(self._name, "$lte", other)

    # Rich comparisons intentionally build MongoDB expressions instead of booleans.
    def __eq__(self, other: Any) -> Expression:  # ty: ignore[invalid-method-override]
        return Expression(self._name, "$eq", other)

    def __ne__(self, other: Any) -> Expression:  # ty: ignore[invalid-method-override]
        return Expression(self._name, "$ne", other)

    def __gt__(self, other: Any) -> Expression:
        return Expression(self._name, "$gt", other)

    def __ge__(self, other: Any) -> Expression:
        return Expression(self._name, "$gte", other)

    def __hash__(self) -> int:
        return super().__hash__()

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)

        model_class = self.model_class
        model_fields = getattr(model_class, "__mongoz_fields__", None)
        if model_class is None or not isinstance(model_fields, dict):
            raise InvalidKeyError(
                f"Field {self._name!r} has no related document attribute {name!r}."
            )

        if name not in model_fields:
            raise InvalidKeyError(f"Model {model_class.__name__!r} has no attribute {name!r}.")

        child_field: MongozField = model_fields[name]
        return MongozField(
            pydantic_field=child_field.pydantic_field,
            model_class=child_field.model_class,
            parent=self,
        )

    def __deepcopy__(self, memo: str) -> Any:
        obj = self.__class__(
            model_class=self.model_class,
            pydantic_field=self.pydantic_field,
            parent=self.parent,
        )
        obj.__dict__ = self.__dict__
        return obj
