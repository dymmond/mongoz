from enum import Enum


class OrderEnum(str, Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return str(self)


class ExpressionOperator(str, Enum):
    IN = "$in"
    NOT_IN = "$nin"
    EQUAL = "$eq"
    NOT_EQUAL = "$ne"
    PATTERN = "$regex"
    WHERE = "$where"
    GREATER_THAN_EQUAL = "$gte"
    GREATER_THAN = "$gt"
    LESS_THAN_EQUAL = "$lte"
    LESS_THAN = "$lt"
    AND = "$and"
    OR = "$or"
    NOR = "$nor"
    NOT = "$not"
    EXISTS = "$exists"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return str(self)
