import decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Optional,
    Pattern,
    Sequence,
    Type,
    Union,
)

from pydantic._internal import _repr
from pydantic._internal._schema_generation_shared import (
    GetJsonSchemaHandler as GetJsonSchemaHandler,
)
from pydantic.fields import FieldInfo

from mongoz.core.connection.database import Database
from mongoz.core.connection.registry import Registry
from mongoz.core.db.querysets.expressions import Expression
from mongoz.exceptions import InvalidKeyError
from mongoz.types import Undefined

if TYPE_CHECKING:
    from mongoz import Document, EmbeddedDocument

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
        parent: Union[Type["FieldInfo"], None] = None,
        model_class: Union["Document", "EmbeddedDocument", None] = None,
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

        self.parent = parent
        self.model_class = model_class
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


class MongozField:
    def __init__(
        self,
        pydantic_field: "BaseField",
        parent: Optional["MongozField"] = None,
        model_class: Union["Document", "EmbeddedDocument", None] = None,
    ) -> None:
        self.model_class = model_class
        self.parent = parent
        self.pydantic_field = pydantic_field

    @property
    def _name(self) -> str:
        if self.parent:
            return self.parent._name + "." + self.pydantic_field.alias
        return self.pydantic_field.alias

    def __lt__(self, other: Any) -> Expression:
        return Expression(self._name, "$lt", other)

    def __le__(self, other: Any) -> Expression:
        return Expression(self._name, "$lte", other)

    def __eq__(self, other: Any) -> Expression:  # type: ignore[override]
        return Expression(self._name, "$eq", other)

    def __ne__(self, other: Any) -> Expression:  # type: ignore[override]
        return Expression(self._name, "$ne", other)

    def __gt__(self, other: Any) -> Expression:
        return Expression(self._name, "$gt", other)

    def __ge__(self, other: Any) -> Expression:
        return Expression(self._name, "$gte", other)

    def __hash__(self) -> int:
        return super().__hash__()

    def __getattr__(self, name: str) -> Any:
        assert self.model_class is not None

        if name not in self.model_class.__mongoz_fields__:
            raise InvalidKeyError(
                f"Model '{self.model_class.__class__.__name__}' has no attribute '{name}'"
            )

        child_field: Type[MongozField] = self.model_class.__mongoz_fields__[name]
        return MongozField(
            pydantic_field=child_field.pydantic_field,
            model_class=child_field.model_class,
            parent=self,
        )

    def __deepcopy__(self, memo: str) -> Any:
        obj = self.__class__(
            model_class=self.model_class, pydantic_field=self.pydantic_field, parent=self.parent
        )
        obj.__dict__ = self.__dict__
        return obj
