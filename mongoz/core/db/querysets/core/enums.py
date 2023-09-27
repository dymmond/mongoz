from enum import Enum


class OrderEnum(str, Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"
