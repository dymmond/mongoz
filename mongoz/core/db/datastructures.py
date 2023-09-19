import enum
from typing import Any, List, Tuple, Union

import pymongo


class Order(int, enum.Enum):
    ASCENDING = pymongo.ASCENDING
    DESCENDING = pymongo.DESCENDING


class IndexType(str, enum.Enum):
    GEO2D = pymongo.GEO2D
    GEOSPHERE = pymongo.GEOSPHERE
    HASHED = pymongo.HASHED
    TEXT = pymongo.TEXT


class Index(pymongo.IndexModel):
    """
    Class responsible for handling and declaring the database indexes.
    """

    def __init__(
        self,
        key: Union[str, None] = None,
        keys: List[Union[Tuple[str, Order], Tuple[str, IndexType]]] = None,
        name: str = None,
        background: bool = False,
        unique: bool = False,
        sparse: bool = False,
        **kwargs: Any,
    ) -> None:
        keys = [(key, Order.ASCENDING)] if key else keys or []
        self.name = name or "_".join([key[0] for key in keys])
        self.unique = unique

        kwargs["name"] = self.name
        kwargs["background"] = background
        kwargs["sparse"] = sparse
        kwargs["unique"] = unique
        return super().__init__(keys, **kwargs)
