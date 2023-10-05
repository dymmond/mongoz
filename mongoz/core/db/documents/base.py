import copy
from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Mapping, Type, Union

import bson
import pydantic
from pydantic import BaseModel, ConfigDict
from pydantic_core._pydantic_core import SchemaValidator as SchemaValidator

from mongoz.core.db.documents._internal import DescriptiveMeta
from mongoz.core.db.documents.document_proxy import ProxyDocument
from mongoz.core.db.documents.metaclasses import BaseModelMeta, MetaInfo
from mongoz.core.db.fields.base import MongozField
from mongoz.core.db.fields.core import ObjectId
from mongoz.core.db.querysets.base import Manager, QuerySet
from mongoz.core.db.querysets.expressions import Expression
from mongoz.core.signals.signal import Signal
from mongoz.core.utils.documents import generify_model_fields
from mongoz.utils.mixins import is_operation_allowed

if TYPE_CHECKING:
    from mongoz import Document
    from mongoz.core.signals import Broadcaster


class BaseMongoz(BaseModel, metaclass=BaseModelMeta):
    """
    Base of all Mongoz models with the core setup.
    """

    __db_document__: ClassVar[bool] = False
    __proxy_document__: ClassVar[Union[Type["Document"], None]] = None

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        json_encoders={bson.ObjectId: str, Signal: str},
        validate_assignment=True,
    )
    is_proxy_document: ClassVar[bool] = False
    meta: ClassVar[MetaInfo] = MetaInfo(None)
    Meta: ClassVar[DescriptiveMeta] = DescriptiveMeta()
    objects: ClassVar[Manager] = Manager()

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.is_proxy_document:
            values = self.extract_default_values_from_field(is_proxy=True, **data)
            self.__dict__ = values  # type: ignore
        else:
            self.extract_default_values_from_field()

    def extract_default_values_from_field(
        self, is_proxy: bool = False, **kwargs: Any
    ) -> Union[Dict[str, Any], None]:
        """
        Populate the defaults of each Mongoz field if any is passed.

        E.g.: DateTime(auto_now=True) will generate the default for automatic
        dates.
        """
        fields: Dict[str, Any] = kwargs if is_proxy else self.model_dump()

        kwargs = {k: v for k, v in fields.items() if k in self.model_fields}
        for key, value in kwargs.items():
            if key not in self.meta.fields:
                if not hasattr(self, key):
                    raise ValueError(f"Invalid keyword {key} for class {self.__class__.__name__}")

            # For non values. Example: bool
            if value is not None:
                # Checks if the default is a callable and executes it.
                if callable(value):
                    setattr(self, key, value())
                else:
                    setattr(self, key, value)
                continue

            # Validate the default fields
            field = self.model_fields[key]
            if hasattr(field, "has_default") and field.has_default():
                setattr(self, key, field.get_default_value())
                continue

            if is_proxy:
                kwargs[key] = value

        return kwargs if is_proxy else None

    def get_instance_name(self) -> str:
        """
        Returns the name of the class in lowercase.
        """
        return self.__class__.__name__.lower()

    @classmethod
    def generate_proxy_document(cls) -> Type["Document"]:
        """
        Generates a proxy document for each model. This proxy model is a simple
        shallow copy of the original model being generated.
        """
        if cls.__proxy_document__:
            return cls.__proxy_document__

        fields = {key: copy.copy(field) for key, field in cls.meta.fields.items()}
        proxy_document = ProxyDocument(
            name=cls.__name__,
            module=cls.__module__,
            metadata=cls.meta,
            definitions=fields,
        )
        proxy_document.build()
        proxy_document.model.model_config["validate_assignment"] = False
        generify_model_fields(proxy_document.model, exclude={"id"})
        return proxy_document.model

    @classmethod
    def query(
        cls: Type["BaseMongoz"], *values: Union[bool, Dict, Expression]
    ) -> QuerySet["Document"]:
        """Filter query criteria nad blocks abstract class operations"""
        is_operation_allowed(cls)

        filter_by: List[Expression] = []
        if not values:
            return QuerySet(model_class=cls)

        for arg in values:
            assert isinstance(arg, (dict, Expression)), "Invalid argument to Query"
            if isinstance(arg, dict):
                query_expressions = Expression.unpack(arg)
                filter_by.extend(query_expressions)
            else:
                filter_by.append(arg)

        return QuerySet(model_class=cls, filter_by=filter_by)

    @property
    def signals(self) -> "Broadcaster":
        return self.__class__.signals  # type: ignore

    @cached_property
    def proxy_document(self) -> Any:
        return self.__class__.proxy_document

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self}>"

    def __str__(self) -> str:
        if not hasattr(self, "id"):
            return f"{self.__class__.__name__}(id={None})"
        return f"{self.__class__.__name__}(id={self.id})"


class MongozBaseModel(BaseMongoz):
    __mongoz_fields__: ClassVar[Mapping[str, Type["MongozField"]]]
    id: Union[ObjectId, None] = pydantic.Field(alias="_id")

    def model_dump(self, show_id: bool = False, **kwargs: Any) -> Dict[str, Any]:
        """
        Args:
            show_pk: bool - Enforces showing the id in the model_dump.
        """
        model = super().model_dump(**kwargs)
        if "id" not in model and show_id:
            model = {**{"id": self.id}, **model}
        return model
