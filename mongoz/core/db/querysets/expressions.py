import collections
import typing
from typing import TYPE_CHECKING, Any, Dict, List, Union, cast

from mongoz.core.db.datastructures import Order

if TYPE_CHECKING:  # pragma: no cover
    from mongoz.core.db.fields.base import MongozField


class Expression:
    def __init__(
        self,
        key: Union[str, "MongozField"],
        operator: str,
        value: Any,
        options: Union[Any, None] = None,
    ) -> None:
        self.key = key if isinstance(key, str) else key._name
        self.operator = operator
        self.value = value
        self.options = options

    @property
    def compiled_value(self) -> Any:
        if isinstance(self.value, list):
            return [self.map(v) for v in self.value]
        else:
            return self.map(self.value)

    def map(self, v: Any) -> Any:
        try:
            return v.model_dump()
        except AttributeError:
            return v

    def compile(self) -> Dict[str, Dict[str, Any]]:
        if not self.options:
            return {self.key: {self.operator: self.compiled_value}}
        return {self.key: {self.operator: self.compiled_value, "$options": self.options}}

    @classmethod
    def compile_many(cls, expressions: List["Expression"]) -> Dict[str, Dict[str, Any]]:
        compiled_dicts: Dict[Any, dict] = collections.defaultdict(dict)
        compiled_lists: Dict[Any, list] = collections.defaultdict(list)

        for expr in expressions:
            for key, value in expr.compile().items():
                # Logical operators need a {"$or": [...]} query
                if key in ["$and", "$or"]:
                    list_value = value.get(key, value.get("$eq"))
                    assert isinstance(list_value, (list, tuple))
                    values = [v.compile() if isinstance(v, Expression) else v for v in list_value]
                    compiled_lists[key] = values
                else:
                    values_dict: Dict[str, Any] = {}
                    for k, v in value.items():
                        if isinstance(v, Expression) and k in ["$not"]:
                            values_dict[k] = {v.operator: v.compiled_value}
                            compiled_dicts[key].update(values_dict)
                        else:
                            compiled_dicts[key].update(value)
        return cast(Dict[str, Dict[str, Any]], {**compiled_dicts, **compiled_lists})

    @classmethod
    def unpack(cls, d: Dict[str, Any]) -> "List[Expression]":
        """Unpack dictionary to a list of Expression.

        For now works only for the following queries:
            d = {"name": "value"}
            d = {"year": {"$gt": 1990}}
            d = {"year": {"$gt": 1990, "$lt": 2000}}
        """
        expressions: List[Expression] = []

        for key, value in d.items():
            if isinstance(value, dict):
                for op, v in value.items():
                    expr = Expression(key=key, operator=op, value=v)
                    expressions.append(expr)
            else:
                expr = Expression(key=key, operator="$eq", value=value)
                expressions.append(expr)
        return expressions


class SortExpression:
    def __init__(self, key: typing.Union[str, "MongozField"], direction: Order) -> None:
        self.key = key if isinstance(key, str) else key._name
        self.direction = direction

    def compile(self) -> typing.Tuple[str, Order]:
        return self.key, self.direction
