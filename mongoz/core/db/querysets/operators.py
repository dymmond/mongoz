import re
from typing import TYPE_CHECKING, Any, List, Union

from mongoz.exceptions import FieldDefinitionError

if TYPE_CHECKING:
    from mongoz.core.db.datastructures import Order
    from mongoz.core.db.querysets.expressions import Expression, SortExpression


class Q:
    """Shortcut for creating Expression type instances."""

    @classmethod
    def asc(cls, key: Any) -> SortExpression:
        return SortExpression(key, Order.ASCENDING)

    @classmethod
    def desc(cls, key: Any) -> SortExpression:
        return SortExpression(key, Order.DESCENDING)

    @classmethod
    def in_(cls, key: Any, values: List) -> Expression:
        return Expression(key=key, operator="$in", value=values)

    @classmethod
    def not_in(cls, key: Any, values: List) -> Expression:
        return Expression(key=key, operator="$nin", value=values)

    @classmethod
    def and_(cls, *args: Union[bool, Expression]) -> Expression:
        assert not isinstance(args, bool)
        return Expression(key="$and", operator="$and", value=args)

    @classmethod
    def or_(cls, *args: Union[bool, Expression]) -> Expression:
        assert not isinstance(args, bool)
        return Expression(key="$or", operator="$or", value=args)

    @classmethod
    def contains(cls, key: Any, value: Any) -> Expression:
        if key.annotation is str:
            return Expression(key=key, operator="$regex", value=value)
        return Expression(key=key, operator="$eq", value=value)

    @classmethod
    def pattern(cls, key: Any, value: Union[str, re.Pattern]) -> Expression:
        if key.annotation is str:
            expression = value.pattern if isinstance(value, re.Pattern) else value
            return Expression(key=key, operator="$regex", value=expression)
        name = key if isinstance(key, str) else key.name
        raise FieldDefinitionError(f"The {name} field is not of type str")
