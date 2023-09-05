import datetime
import decimal
import enum
import uuid
from enum import EnumMeta
from typing import TYPE_CHECKING, Any, Generator, List, Optional, Sequence, Set, Tuple, Type, Union

import bson
import pydantic
from pydantic import EmailStr

from mongoz.core.db.fields.base import BaseField
from mongoz.exceptions import FieldDefinitionError

if TYPE_CHECKING:
    from mongoz.core.db.documents.document import Document


CLASS_DEFAULTS = ["cls", "__class__", "kwargs"]


class FieldFactory:
    """The base for all model fields to be used with Mongoz"""

    _bases = (BaseField,)
    _type: Any = None

    def __new__(cls, *args: Any, **kwargs: Any) -> BaseField:  # type: ignore
        cls.validate(**kwargs)

        default = kwargs.pop("default", None)
        null: bool = kwargs.pop("null", False)
        unique: bool = kwargs.pop("unique", False)
        index: bool = kwargs.pop("index", False)
        name: str = kwargs.pop("name", None)
        choices: Set[Any] = set(kwargs.pop("choices", []))
        comment: str = kwargs.pop("comment", None)
        owner = kwargs.pop("owner", None)
        read_only: bool = kwargs.pop("read_only", False)
        list_type: type = kwargs.pop("list_type", None)

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
            **kwargs,
        )
        Field = type(cls.__name__, cls._bases, {})
        return Field(**namespace)  # type: ignore

    @classmethod
    def validate(cls, **kwargs: Any) -> None:  # pragma no cover
        """
        Used to validate if all required parameters on a given field type are set.
        :param kwargs: all params passed during construction
        :type kwargs: Any
        """


class ObjectId(FieldFactory, bson.ObjectId):
    _type: bson.ObjectId

    @classmethod
    def __get_validators__(cls) -> Generator[bson.ObjectId, None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, **kwargs: Any) -> bson.ObjectId:
        if not bson.ObjectId.is_valid(**kwargs):
            raise ValueError("Invalid value for ObjectId")
        return bson.ObjectId(**kwargs)


class String(FieldFactory, str):
    """String field representation that constructs the Field class and populates the values"""

    _type = str

    def __new__(  # type: ignore
        cls,
        *,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        **kwargs: Any,
    ) -> BaseField:
        kwargs = {
            **kwargs,
            **{key: value for key, value in locals().items() if key not in CLASS_DEFAULTS},
        }

        return super().__new__(cls, **kwargs)

    # @classmethod
    # def validate(cls, **kwargs: Any) -> None:
    #     max_length = kwargs.get("max_length", 0)
    #     if max_length <= 0:
    #         raise FieldDefinitionError(detail=f"'max_length' is required for {cls.__name__}")

    #     min_length = kwargs.get("min_length")

    #     assert min_length is None or isinstance(min_length, int)
    #     assert max_length is None or isinstance(max_length, int)


class Number(FieldFactory):
    @classmethod
    def validate(cls, **kwargs: Any) -> None:
        minimum = kwargs.get("minimum", None)
        maximum = kwargs.get("maximum", None)

        if (minimum is not None and maximum is not None) and minimum > maximum:
            raise FieldDefinitionError(detail="'minimum' cannot be bigger than 'maximum'")


class Integer(Number, int):
    """
    Integer field factory that construct Field classes and populated their values.
    """

    _type = int

    def __new__(  # type: ignore
        cls,
        *,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
        multiple_of: Optional[int] = None,
        **kwargs: Any,
    ) -> BaseField:
        autoincrement = kwargs.pop("autoincrement", None)
        autoincrement = (
            autoincrement if autoincrement is not None else kwargs.get("primary_key", False)
        )
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in ["cls", "__class__", "kwargs"]},
        }
        return super().__new__(cls, **kwargs)


class Double(Number, float):
    """Representation of a int32 and int64"""

    _type = float

    def __new__(  # type: ignore
        cls,
        *,
        mininum: Optional[float] = None,
        maximun: Optional[float] = None,
        multiple_of: Optional[int] = None,
        **kwargs: Any,
    ) -> BaseField:
        kwargs = {
            **kwargs,
            **{key: value for key, value in locals().items() if key not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class Decimal(Number, decimal.Decimal):
    _type = decimal.Decimal

    def __new__(  # type: ignore
        cls,
        *,
        minimum: float = None,
        maximum: float = None,
        multiple_of: int = None,
        max_digits: int = None,
        decimal_places: int = None,
        **kwargs: Any,
    ) -> BaseField:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in ["cls", "__class__", "kwargs"]},
        }
        return super().__new__(cls, **kwargs)

    @classmethod
    def validate(cls, **kwargs: Any) -> None:
        super().validate(**kwargs)

        max_digits = kwargs.get("max_digits")
        decimal_places = kwargs.get("decimal_places")
        if max_digits is None or max_digits < 0 or decimal_places is None or decimal_places < 0:
            raise FieldDefinitionError(
                "max_digits and decimal_places are required for DecimalField"
            )


class Boolean(FieldFactory, int):
    """Representation of a boolean"""

    _type = bool

    def __new__(  # type: ignore
        cls,
        *,
        default: Optional[bool] = False,
        **kwargs: Any,
    ) -> BaseField:
        kwargs = {
            **kwargs,
            **{key: value for key, value in locals().items() if key not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class AutoNowMixin(FieldFactory):
    def __new__(  # type: ignore
        cls,
        *,
        auto_now: Optional[bool] = False,
        auto_now_add: Optional[bool] = False,
        **kwargs: Any,
    ) -> BaseField:
        if auto_now_add and auto_now:
            raise FieldDefinitionError("'auto_now' and 'auto_now_add' cannot be both True")

        if auto_now_add or auto_now:
            kwargs["read_only"] = True

        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class DateTime(AutoNowMixin, datetime.datetime):
    """Representation of a datetime field"""

    _type = datetime.datetime

    def __new__(  # type: ignore
        cls,
        *,
        auto_now: Optional[bool] = False,
        auto_now_add: Optional[bool] = False,
        **kwargs: Any,
    ) -> BaseField:
        if auto_now_add or auto_now:
            kwargs["default"] = datetime.datetime.now

        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class Date(AutoNowMixin, datetime.date):
    """Representation of a date field"""

    _type = datetime.date

    def __new__(  # type: ignore
        cls,
        *,
        auto_now: Optional[bool] = False,
        auto_now_add: Optional[bool] = False,
        **kwargs: Any,
    ) -> BaseField:
        if auto_now_add or auto_now:
            kwargs["default"] = datetime.date.today

        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class Time(FieldFactory, datetime.time):
    """Representation of a time field"""

    _type = datetime.time

    def __new__(cls, **kwargs: Any) -> BaseField:  # type: ignore
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)


class Object(FieldFactory, pydantic.Json):  # type: ignore
    """Representation of a JSONField"""

    _type = Any


class Binary(FieldFactory, bytes):
    """Representation of a binary"""

    _type = bytes

    def __new__(cls, *, max_length: Optional[int] = 0, **kwargs: Any) -> BaseField:  # type: ignore
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)

    @classmethod
    def validate(cls, **kwargs: Any) -> None:
        max_length = kwargs.get("max_length", None)
        if max_length <= 0:
            raise FieldDefinitionError(detail="Parameter 'max_length' is required for BinaryField")


class UUID(FieldFactory, uuid.UUID):
    """Representation of a uuid"""

    _type = uuid.UUID

    def __new__(cls, **kwargs: Any) -> BaseField:  # type: ignore
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }

        return super().__new__(cls, **kwargs)


class Choice(FieldFactory):
    """Representation of an Enum"""

    _type = enum.Enum

    def __new__(  # type: ignore
        cls,
        choices: Optional[Sequence[Union[Tuple[str, str], Tuple[str, int]]]] = None,
        **kwargs: Any,
    ) -> BaseField:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        return super().__new__(cls, **kwargs)

    @classmethod
    def validate(cls, **kwargs: Any) -> None:
        choice_class = kwargs.get("choices")
        if choice_class is None or not isinstance(choice_class, EnumMeta):
            raise FieldDefinitionError("ChoiceField choices must be an Enum")


class EmailField(String):
    _type = EmailStr


class Array(FieldFactory, list):
    _type = list

    def __new__(  # type: ignore
        cls,
        document: type,
        **kwargs: Any,
    ) -> BaseField:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        kwargs["list_type"] = document
        return super().__new__(cls, **kwargs)


class ArrayList(FieldFactory, list):
    _type = list

    def __new__(  # type: ignore
        cls,
        **kwargs: Any,
    ) -> BaseField:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        kwargs["list_type"] = Any
        return super().__new__(cls, **kwargs)


class Embed(FieldFactory):
    _type = None

    def __new__(  # type: ignore
        cls,
        document: Type["Document"],
        **kwargs: Any,
    ) -> BaseField:
        kwargs = {
            **kwargs,
            **{k: v for k, v in locals().items() if k not in CLASS_DEFAULTS},
        }
        cls._type = document
        return super().__new__(cls, **kwargs)

    @classmethod
    def validate(cls, **kwargs: Any) -> None:
        from mongoz.core.db.documents.document import Document, EmbeddedDocument

        document = kwargs.get("document")
        if not issubclass(document, (Document, EmbeddedDocument)):
            raise FieldDefinitionError(
                "'document' must be of type mongoz.Document or mongoz.EmbeddedDocument"
            )
