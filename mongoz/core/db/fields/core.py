from __future__ import annotations

import datetime
import decimal
import importlib
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generator,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
)

import bson
import pydantic
import pydantic_core
from bson.decimal128 import Decimal128
from pydantic import EmailStr, ValidationError
from pydantic._internal._schema_generation_shared import (
    GetJsonSchemaHandler as GetJsonSchemaHandler,
)
from pydantic.json_schema import JsonSchemaValue as JsonSchemaValue
from pydantic_core import InitErrorDetails
from pydantic_core.core_schema import (
    CoreSchema,
    with_info_plain_validator_function as general_plain_validator_function,
)

from mongoz.core.db.fields.base import BaseField
from mongoz.exceptions import FieldDefinitionError

mongoz_setattr = object.__setattr__

if TYPE_CHECKING:
    from mongoz.core.db.documents.document import Document, EmbeddedDocument


CLASS_DEFAULTS = ["cls", "__class__", "kwargs"]
FieldValue = TypeVar("FieldValue")
NumberValue = TypeVar("NumberValue", int, float, decimal.Decimal)
EmbeddedValue = TypeVar("EmbeddedValue", bound="EmbeddedDocument")
ArrayValue = TypeVar("ArrayValue")


class FieldFactory(Generic[FieldValue]):
    """The base for all model fields to be used with Mongoz"""

    _bases = (BaseField,)
    _type: Any = None

    def __new__(cls, *args: Any, **kwargs: Any) -> FieldValue:
        cls.validate_field(**kwargs)

        default = kwargs.pop("default", None)
        null: bool = kwargs.pop("null", False)
        unique: bool = kwargs.pop("unique", False)
        index: bool = kwargs.pop("index", False)
        name: str = kwargs.pop("name", None)
        choices: Set[Any] = set(kwargs.pop("choices", []))
        comment: str = kwargs.pop("comment", None)
        owner = kwargs.pop("owner", None)
        read_only: bool = kwargs.pop("read_only", False)
        list_type: Any = kwargs.pop("list_type", None)
        sparse: bool = kwargs.pop("sparse", False)

        if list_type is None:
            field_type = cls._type
        else:
            field_type = List[list_type]

        namespace = dict(
            __type__=field_type,
            annotation=field_type,
            name=name,
            default=default,
            null=null,
            index=index,
            unique=unique,
            choices=choices,
            comment=comment,
            owner=owner,
            read_only=read_only,
            sparse=sparse,
            **kwargs,
        )
        Field = type(cls.__name__, cls._bases, {})
        # Monkey patch the validation functionality.
        Field.validate_field_value = cls.validate_field_value
        return cast(FieldValue, Field(**namespace))

    @classmethod
    def validate_field(cls, **kwargs: Any) -> None:  # pragma no cover
        ...

    @staticmethod
    def validate_field_value(field: BaseField, value: object) -> object:
        return value


class ObjectId(bson.ObjectId):
    def __init__(
        self,
        oid: Union[str, bson.ObjectId, bytes, None] = None,
        null: bool = False,
    ) -> None:
        super().__init__(oid)
        self.null = null
        self.name: Union[str, None] = None

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Any], None, None]:
        def validator(value: Any) -> Any:
            return cls.validate(value)

        yield validator

    @classmethod
    def validate(cls: Type["bson.ObjectId"], v: Any) -> Any:
        if not isinstance(v, bson.ObjectId):
            raise ValueError(f"Expected ObjectId, got: {type(v)}")
        return v

    @classmethod
    def _validate(cls, __input_value: Any, _: Any) -> "ObjectId":
        if not isinstance(__input_value, bson.ObjectId):
            raise ValueError(f"Expected ObjectId, got: {type(__input_value)}")
        if not bson.ObjectId.is_valid(__input_value):
            raise ValueError("Invalid value for ObjectId")
        return cast(ObjectId, __input_value)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string"}

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: Callable[[Any], CoreSchema]
    ) -> CoreSchema:
        return general_plain_validator_function(cls._validate)


class NullableObjectId(FieldFactory[ObjectId], ObjectId):
    _type = ObjectId

    def __new__(
        cls,
        null: bool = True,
        **kwargs: Any,
    ) -> ObjectId:
        kwargs = {
            **kwargs,
            **{key: value for key, value in locals().items() if key not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class ForeignKey(FieldFactory[ObjectId], ObjectId):
    """
    Foregin field refresents the foreign refrenced Document or EmbeddedDocument.
    """

    _type = ObjectId

    def __new__(
        cls,
        refer_to: Union[Type["Document"], Type["EmbeddedDocument"], str],
        null: bool = False,
        **kwargs: Any,
    ) -> ObjectId:
        kwargs = {
            **kwargs,
            **{key: value for key, value in locals().items() if key not in CLASS_DEFAULTS},
        }
        field = cast(BaseField, super().__new__(cls, **kwargs))

        def lazy_resolve_model(
            self: BaseField,
        ) -> type[Union["Document", "EmbeddedDocument"]]:
            if isinstance(field.refer_to, str):
                module_path, class_name = field.refer_to.rsplit(".", 1)
                module = importlib.import_module(module_path)
                model = getattr(module, class_name)
                return model
            assert field.refer_to is not None
            return field.refer_to

        # Monkey-patch `.to`  as a property
        property_name = "to"
        setattr(field.__class__, property_name, property(lazy_resolve_model))
        return cast(ObjectId, field)


class String(FieldFactory[str], str):
    """String field representation that constructs the Field class and populates the values"""

    _type = str

    def __new__(
        cls,
        *,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        kwargs = {
            **kwargs,
            **{key: value for key, value in locals().items() if key not in CLASS_DEFAULTS},
        }

        return super().__new__(cls, **kwargs)


class Number(FieldFactory[NumberValue], Generic[NumberValue]):
    @classmethod
    def validate_field(cls, **kwargs: Any) -> None:
        minimum = kwargs.get("minimum", None)
        maximum = kwargs.get("maximum", None)

        if (minimum is not None and maximum is not None) and minimum > maximum:
            raise FieldDefinitionError(detail="'minimum' cannot be bigger than 'maximum'")

    @staticmethod
    def validate_field_value(field: BaseField, value: object) -> object:
        if not isinstance(value, (int, float, decimal.Decimal)):
            return value
        errors: List[InitErrorDetails] = []
        alias = field.alias or field.name or ""
        if field.minimum and field.minimum > value:
            errors.append(
                {
                    "loc": (alias,),
                    "input": value,
                    "type": pydantic_core.PydanticCustomError(
                        "value_error",
                        "Value must be greater than or equals to {minimum}",
                        {"minimum": field.minimum},
                    ),
                }
            )
        if field.maximum and field.maximum < value:
            errors.append(
                {
                    "loc": (alias,),
                    "input": value,
                    "type": pydantic_core.PydanticCustomError(
                        "value_error",
                        "Value must be less than or equals to {maximum}",
                        {"maximum": field.maximum},
                    ),
                }
            )
        if errors:
            raise ValidationError.from_exception_data(
                title=f"Validation error for field {alias}",
                line_errors=errors,
            )
        return value


class Integer(Number[int], int):
    """
    Integer field factory that construct Field classes and populated their values.
    """

    _type = int

    def __new__(
        cls,
        *,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
        multiple_of: Optional[int] = None,
        **kwargs: Any,
    ) -> int:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in ["cls", "__class__", "kwargs"]},
        }
        return super().__new__(cls, **kwargs)


class Double(Number[float], float):
    """Representation of a int32 and int64"""

    _type = float

    def __new__(
        cls,
        *,
        mininum: Optional[float] = None,
        maximun: Optional[float] = None,
        multiple_of: Optional[int] = None,
        **kwargs: Any,
    ) -> float:
        kwargs = {
            **kwargs,
            **{key: value for key, value in locals().items() if key not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class Decimal(Number[decimal.Decimal], decimal.Decimal):
    _type = Union[decimal.Decimal, Decimal128]

    def __new__(
        cls,
        *,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        multiple_of: Optional[int] = None,
        max_digits: Optional[int] = None,
        decimal_places: Optional[int] = None,
        **kwargs: Any,
    ) -> decimal.Decimal:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in ["cls", "__class__", "kwargs"]},
        }
        return super().__new__(cls, **kwargs)

    @classmethod
    def validate_field(cls, **kwargs: Any) -> None:
        super().validate_field(**kwargs)

        max_digits = kwargs.get("max_digits")
        decimal_places = kwargs.get("decimal_places")
        if max_digits is None or max_digits < 0 or decimal_places is None or decimal_places < 0:
            raise FieldDefinitionError(
                "max_digits and decimal_places are required for DecimalField"
            )

    @staticmethod
    def validate_field_value(field: BaseField, value: object) -> object:
        if not isinstance(value, (int, float, str, decimal.Decimal)):
            return value
        errors: List[InitErrorDetails] = []
        alias = field.alias or field.name or ""
        dec = decimal.Decimal(str(value))

        def get_decimal_parts(
            value: Union[int, float, str, decimal.Decimal],
        ) -> tuple[int, int, int]:
            dec = decimal.Decimal(str(value))
            # Precision check
            sign, digits, exponent = dec.as_tuple()
            digits_count = len(digits)

            # Count fractional digits
            frac_digit = -exponent if isinstance(exponent, int) and exponent < 0 else 0
            int_digits = digits_count - frac_digit
            return int_digits, frac_digit, digits_count

        if field.minimum and field.minimum > dec:
            errors.append(
                {
                    "loc": (alias,),
                    "input": value,
                    "type": pydantic_core.PydanticCustomError(
                        "value_error",
                        "Value must be greater than or equals to {minimum}",
                        {"minimum": field.minimum},
                    ),
                }
            )
        if field.maximum and field.maximum < dec:
            errors.append(
                {
                    "loc": (alias,),
                    "input": value,
                    "type": pydantic_core.PydanticCustomError(
                        "value_error",
                        "Value must be less than or equals to {maximum}",
                        {"maximum": field.maximum},
                    ),
                }
            )

        # Rule 1: Fractional digits <= scale

        int_digits, frac_digit, digits_count = get_decimal_parts(value)
        assert field.decimal_places is not None
        if frac_digit > field.decimal_places:
            value = float(
                dec.quantize(
                    decimal.Decimal(10) ** -field.decimal_places,
                    rounding=decimal.ROUND_DOWN,
                )
            )

        # Rule 2: Total digits <= precision
        int_digits, frac_digit, digits_count = get_decimal_parts(value)
        assert field.max_digits is not None
        if digits_count > field.max_digits:
            errors.append(
                {
                    "loc": (alias,),
                    "input": value,
                    "type": pydantic_core.PydanticCustomError(
                        "value_error",
                        "Value must have at most {max_digits} total digits",
                        {"max_digits": field.max_digits},
                    ),
                }
            )
        # Check integer digits
        if int_digits > (field.max_digits - field.decimal_places):
            errors.append(
                {
                    "loc": (alias,),
                    "input": value,
                    "type": pydantic_core.PydanticCustomError(
                        "value_error",
                        ("Value must have at most {whole_digits} digits before the decimal point"),
                        {"whole_digits": field.max_digits - field.decimal_places},
                    ),
                }
            )
        if errors:
            raise ValidationError.from_exception_data(
                title=f"Validation error for field {alias}",
                line_errors=errors,
            )
        return value


class Boolean(FieldFactory[bool], int):
    """Representation of a boolean"""

    _type = bool

    def __new__(
        cls,
        *,
        default: Optional[bool] = False,
        **kwargs: Any,
    ) -> bool:
        kwargs = {
            **kwargs,
            **{key: value for key, value in locals().items() if key not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class AutoNowMixin(FieldFactory[FieldValue], Generic[FieldValue]):
    def __new__(
        cls,
        *,
        auto_now: Optional[bool] = False,
        auto_now_add: Optional[bool] = False,
        **kwargs: Any,
    ) -> FieldValue:
        if auto_now_add and auto_now:
            raise FieldDefinitionError("'auto_now' and 'auto_now_add' cannot be both True")

        if auto_now_add or auto_now:
            kwargs["read_only"] = True

        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class DateTime(AutoNowMixin[datetime.datetime], datetime.datetime):
    """Representation of a datetime field"""

    _type = datetime.datetime

    def __new__(
        cls,
        *,
        auto_now: Optional[bool] = False,
        auto_now_add: Optional[bool] = False,
        **kwargs: Any,
    ) -> datetime.datetime:
        if auto_now_add or auto_now:
            kwargs["default"] = datetime.datetime.now

        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class Date(AutoNowMixin[datetime.date], datetime.date):
    """Representation of a date field"""

    _type = datetime.date

    def __new__(
        cls,
        *,
        auto_now: Optional[bool] = False,
        auto_now_add: Optional[bool] = False,
        **kwargs: Any,
    ) -> datetime.date:
        if auto_now_add or auto_now:
            kwargs["default"] = datetime.date.today

        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class Time(FieldFactory[datetime.time], datetime.time):
    """Representation of a time field"""

    _type = datetime.time

    def __new__(cls, **kwargs: Any) -> datetime.time:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


# Pydantic exposes Json as a runtime class while typing it as an Annotated special form.
JsonBase = cast(Type[Any], pydantic.Json)


class Object(FieldFactory[Dict[str, Any]], JsonBase):
    """Representation of a JSONField"""

    _type = Any


class Binary(FieldFactory[bytes], bytes):
    """Representation of a binary"""

    _type = bytes

    def __new__(cls, *, max_length: Optional[int] = 0, **kwargs: Any) -> bytes:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)

    @classmethod
    def validate_field(cls, **kwargs: Any) -> None:
        max_length = kwargs.get("max_length", None)
        if max_length is None or max_length <= 0:
            raise FieldDefinitionError(detail="Parameter 'max_length' is required for BinaryField")


class UUID(FieldFactory[uuid.UUID], uuid.UUID):
    """Representation of a uuid"""

    _type = uuid.UUID

    def __new__(cls, **kwargs: Any) -> uuid.UUID:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class Email(String):
    _type = EmailStr


class Array(FieldFactory[List[ArrayValue]], list, Generic[ArrayValue]):
    _type = list

    def __new__(
        cls,
        type_of: Type[ArrayValue],
        **kwargs: Any,
    ) -> List[ArrayValue]:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        kwargs["list_type"] = type_of
        return super().__new__(cls, **kwargs)


class ArrayList(FieldFactory[List[Any]], list):
    _type = list

    def __new__(
        cls,
        **kwargs: Any,
    ) -> List[Any]:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        kwargs["list_type"] = Any
        return super().__new__(cls, **kwargs)


class Embed(FieldFactory[EmbeddedValue], Generic[EmbeddedValue]):
    _type = None

    def __new__(
        cls,
        document: Type[EmbeddedValue],
        **kwargs: Any,
    ) -> EmbeddedValue:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        cls._type = document
        return super().__new__(cls, **kwargs)

    @classmethod
    def validate_field(cls, **kwargs: Any) -> None:
        from mongoz.core.db.documents.document import EmbeddedDocument

        document = kwargs.get("document")
        if not isinstance(document, type):
            raise FieldDefinitionError(
                "'document' must be of type mongoz.Document or mongoz.EmbeddedDocument"
            )
        if not issubclass(document, EmbeddedDocument):
            raise FieldDefinitionError(
                "'document' must be of type mongoz.Document or mongoz.EmbeddedDocument"
            )
