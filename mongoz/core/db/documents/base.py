from typing import ClassVar, Dict, List, Mapping, Type, TypeVar, Union

import bson
import pydantic
from pydantic import BaseModel, ConfigDict
from pydantic_core._pydantic_core import SchemaValidator as SchemaValidator
from typing_extensions import Self

from mongoz.core.db.documents._internal import DescriptiveMeta
from mongoz.core.db.documents.metaclasses import BaseModelMeta, MetaInfo
from mongoz.core.db.fields.base import BaseField
from mongoz.core.db.fields.core import ObjectId
from mongoz.core.db.querysets.base import QuerySet
from mongoz.core.db.querysets.expressions import Expression
from mongoz.core.utils.models import DateParser, ModelParser

T = TypeVar("T", bound="MongozBaseModel")


class BaseMongoz(BaseModel, DateParser, ModelParser, metaclass=BaseModelMeta):
    """
    Base of all Mongoz models with the core setup.
    """

    __db_model__: ClassVar[bool] = False

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        json_encoders={bson.ObjectId: str},
        validate_assignment=True,
    )

    parent: ClassVar[Union[Type[Self], None]]
    meta: ClassVar[MetaInfo] = MetaInfo(None)
    Meta: ClassVar[DescriptiveMeta] = DescriptiveMeta()

    def get_instance_name(self) -> str:
        """
        Returns the name of the class in lowercase.
        """
        return self.__class__.__name__.lower()

    @classmethod
    def query(cls: Type[T], *values: Union[bool, Dict, Expression]) -> QuerySet[T]:
        """Filter query criteria."""
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

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self}>"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.pk})"


class MongozBaseModel(BaseMongoz):
    __mongoz_fields__: ClassVar[Mapping[str, Type["BaseField"]]]
    id: Union[ObjectId, None] = pydantic.Field(alias="_id")
