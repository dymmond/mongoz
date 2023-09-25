import re
from typing import Any, List, Union

from mongoz.core.db.datastructures import Order
from mongoz.core.db.querysets.expressions import Expression, SortExpression
from mongoz.exceptions import FieldDefinitionError


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
    def eq(cls, key: Any, *args: Union[bool, Expression]) -> Expression:
        assert not isinstance(args, bool)
        return Expression(key=key, operator="$eq", value=args)

    @classmethod
    def contains(cls, key: Any, value: Any) -> Expression:
        if key.pydantic_field.annotation is str:
            return Expression(key=key, operator="$regex", value=value)
        return Expression(key=key, operator="$eq", value=value)

    @classmethod
    def where(cls, key: Any, value: str) -> Expression:
        assert isinstance(value, str)
        return Expression(key=key, operator="$where", value=value)

    @classmethod
    def pattern(cls, key: Any, value: Union[str, re.Pattern]) -> Expression:
        if key.pydantic_field.annotation is str:
            expression = value.pattern if isinstance(value, re.Pattern) else value
            return Expression(key=key, operator="$regex", value=expression)
        name = key if isinstance(key, str) else key._name
        raise FieldDefinitionError(f"The {name} field is not of type str")
