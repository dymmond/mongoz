import re
from typing import Any, List, Union

from mongoz.core.db.datastructures import Order
from mongoz.core.db.querysets.expressions import Expression, SortExpression
from mongoz.exceptions import FieldDefinitionError
from mongoz.utils.enums import ExpressionOperator


class Ordering:
    """
    All the operators responsible for checking by order.
    """

    @classmethod
    def asc(cls, key: Any) -> SortExpression:
        return SortExpression(key, Order.ASCENDING)

    @classmethod
    def desc(cls, key: Any) -> SortExpression:
        return SortExpression(key, Order.DESCENDING)


class Iterable:
    """
    All the operators responsible for checking comparison
    within a an iterable.
    """

    @classmethod
    def in_(cls, key: Any, values: List) -> Expression:
        return Expression(key=key, operator=ExpressionOperator.IN, value=values)

    @classmethod
    def not_in(cls, key: Any, values: List) -> Expression:
        return Expression(key=key, operator=ExpressionOperator.NOT_IN, value=values)


class Equality:
    """
    All the operators responsible for checking equality comparison.
    """

    @classmethod
    def eq(cls, key: Any, value: Union[bool, Expression]) -> Expression:
        return Expression(key=key, operator=ExpressionOperator.EQUAL, value=value)

    @classmethod
    def neq(cls, key: Any, value: Union[bool, Expression]) -> Expression:
        return Expression(key=key, operator=ExpressionOperator.NOT_EQUAL, value=value)

    @classmethod
    def contains(cls, key: Any, value: Any) -> Expression:
        if isinstance(key, str) or key.pydantic_field.annotation is str:
            return Expression(key=key, operator=ExpressionOperator.PATTERN, value=value)
        return Expression(key=key, operator=ExpressionOperator.EQUAL, value=value)

    @classmethod
    def icontains(cls, key: Any, value: Any) -> Expression:
        if isinstance(key, str) or key.pydantic_field.annotation is str:
            return Expression(
                key=key, operator=ExpressionOperator.PATTERN, value=value, options="i"
            )
        return Expression(key=key, operator=ExpressionOperator.EQUAL, value=value)

    @classmethod
    def where(cls, key: Any, value: str) -> Expression:
        assert isinstance(value, str)
        return Expression(key=key, operator=ExpressionOperator.WHERE, value=value)

    @classmethod
    def pattern(cls, key: Any, value: Union[str, re.Pattern]) -> Expression:
        if isinstance(key, str) or key.pydantic_field.annotation is str:
            expression = value.pattern if isinstance(value, re.Pattern) else value
            return Expression(key=key, operator=ExpressionOperator.PATTERN, value=expression)
        name = key if isinstance(key, str) else key._name
        raise FieldDefinitionError(f"The {name} field is not of type str")


class Comparison:
    """
    All the operators responsible for checking comparison
    by greatness.
    """

    @classmethod
    def gte(cls, key: Any, value: Union[bool, Expression]) -> Expression:
        assert not isinstance(value, bool)
        return Expression(key=key, operator=ExpressionOperator.GREATER_THAN_EQUAL, value=value)

    @classmethod
    def gt(cls, key: Any, value: Union[bool, Expression]) -> Expression:
        assert not isinstance(value, bool)
        return Expression(key=key, operator=ExpressionOperator.GREATER_THAN, value=value)

    @classmethod
    def lt(cls, key: Any, value: Union[bool, Expression]) -> Expression:
        assert not isinstance(value, bool)
        return Expression(key=key, operator=ExpressionOperator.LESS_THAN, value=value)

    @classmethod
    def lte(cls, key: Any, value: Union[bool, Expression]) -> Expression:
        assert not isinstance(value, bool)
        return Expression(key=key, operator=ExpressionOperator.LESS_THAN_EQUAL, value=value)


class Element:
    """
    All element query operators.
    """

    @classmethod
    def exists(cls, key: Any, value: Union[bool, Expression]) -> Expression:
        return Expression(key=key, operator=ExpressionOperator.EXISTS, value=value)


class Q(Ordering, Iterable, Equality, Comparison):
    """
    Shortcut for the creation of an Expression.
    """

    @classmethod
    def and_(cls, *args: Union[bool, Expression]) -> Expression:
        assert not isinstance(args, bool)  # type: ignore
        return Expression(key=ExpressionOperator.AND, operator=ExpressionOperator.AND, value=args)

    @classmethod
    def or_(cls, *args: Union[bool, Expression]) -> Expression:
        assert not isinstance(args, bool)  # type: ignore
        return Expression(key=ExpressionOperator.OR, operator=ExpressionOperator.OR, value=args)

    @classmethod
    def nor_(cls, *args: Union[bool, Expression]) -> Expression:
        return Expression(key=ExpressionOperator.NOR, operator=ExpressionOperator.NOR, value=args)

    @classmethod
    def not_(cls, key: Any, value: Union[bool, Expression]) -> Expression:
        if hasattr(key, "pydantic_field"):
            value = Expression(key=key, operator=ExpressionOperator.EQUAL, value=value)
        return Expression(key=key, operator=ExpressionOperator.NOT, value=value)
