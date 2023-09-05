import copy
from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Sequence, Type, Union

import bson
from pydantic import BaseModel, ConfigDict
from pydantic_core._pydantic_core import SchemaValidator as SchemaValidator
from typing_extensions import Self

from mongoz.core.db.fields.core import ObjectId
from mongoz.core.db.models._internal import DescriptiveMeta
from mongoz.core.db.models.managers import Manager
from mongoz.core.db.models.metaclasses import BaseModelMeta, MetaInfo
from mongoz.core.db.models.model_proxy import ProxyModel
from mongoz.core.utils.models import DateParser, ModelParser, generify_model_fields

if TYPE_CHECKING:
    from mongoz.core.db.fields.base import BaseField
    from mongoz.core.db.models import Document

EXCLUDED_LOOKUP = ["__model_references__", "_table"]


class MongozBaseModel(BaseModel, DateParser, ModelParser, metaclass=BaseModelMeta):
    """
    Base of all Mongoz models with the core setup.
    """

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        json_encoders={bson.ObjectId: str},
        validate_assignment=True,
    )
    id: Optional[ObjectId] = ObjectId(alias="_id")
    parent: ClassVar[Union[Type[Self], None]]
    is_proxy_model: ClassVar[bool] = False

    query: ClassVar[Manager] = Manager()
    meta: ClassVar[MetaInfo] = MetaInfo(None)
    Meta: ClassVar[DescriptiveMeta] = DescriptiveMeta()
    __proxy_model__: ClassVar[Union[Type["Document"], None]] = None
    __db_model__: ClassVar[bool] = False
    __mongoz_fields__: ClassVar[Sequence[Type["BaseField"]]] = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self}>"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.pk})"

    @cached_property
    def proxy_model(self) -> Any:
        return self.__class__.proxy_model

    @classmethod
    def generate_proxy_model(cls) -> Type["Document"]:
        """
        Generates a proxy model for each model. This proxy model is a simple
        shallow copy of the original model being generated.
        """
        if cls.__proxy_model__:
            return cls.__proxy_model__

        fields = {key: copy.copy(field) for key, field in cls.fields.items()}
        proxy_model = ProxyModel(
            name=cls.__name__,
            module=cls.__module__,
            metadata=cls.meta,
            definitions=fields,
        )

        proxy_model.build()
        generify_model_fields(proxy_model.model)
        return proxy_model.model

    def get_instance_name(self) -> str:
        """
        Returns the name of the class in lowercase.
        """
        return self.__class__.__name__.lower()
