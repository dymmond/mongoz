import copy
from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Sequence, Type, Union, cast

import bson
from pydantic import BaseModel, ConfigDict
from pydantic_core._pydantic_core import SchemaValidator as SchemaValidator
from typing_extensions import Self

from mongoz.core.db.models._internal import DescriptiveMeta
from mongoz.core.db.models.managers import Manager
from mongoz.core.db.models.metaclasses import BaseModelMeta, MetaInfo
from mongoz.core.db.models.model_proxy import ProxyModel
from mongoz.core.utils.functional import mongoz_setattr
from mongoz.core.utils.models import DateParser, ModelParser, generify_model_fields

if TYPE_CHECKING:
    from mongoz.core.db.fields.base import BaseField
    from mongoz.core.db.models import Model

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
    parent: ClassVar[Union[Type[Self], None]]
    is_proxy_model: ClassVar[bool] = False

    query: ClassVar[Manager] = Manager()
    meta: ClassVar[MetaInfo] = MetaInfo(None)
    Meta: ClassVar[DescriptiveMeta] = DescriptiveMeta()
    __proxy_model__: ClassVar[Union[Type["Model"], None]] = None
    __db_model__: ClassVar[bool] = False
    __mongoz_fields__: ClassVar[Sequence[Type["BaseField"]]] = None

    @property
    def pk(self) -> Any:
        return getattr(self, self.pkname, None)

    @pk.setter
    def pk(self, value: Any) -> Any:
        mongoz_setattr(self, self.pkname, value)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self}>"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.pkname}={self.pk})"

    @cached_property
    def proxy_model(self) -> Any:
        return self.__class__.proxy_model

    @classmethod
    def generate_proxy_model(cls) -> Type["Model"]:
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

    def model_dump(self, show_pk: bool = False, **kwargs: Any) -> Dict[str, Any]:
        """
        An updated version of the model dump if the primary key is not provided.

        Args:
            show_pk: bool - Enforces showing the primary key in the model_dump.
        """
        model = super().model_dump(**kwargs)
        if self.pkname not in model and show_pk:
            model = {**{self.pkname: self.pk}, **model}
        return model

    def get_instance_name(self) -> str:
        """
        Returns the name of the class in lowercase.
        """
        return self.__class__.__name__.lower()
