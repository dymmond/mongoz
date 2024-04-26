from typing import ClassVar

import mongoz
from mongoz import QuerySetManager

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


class InactiveManager(QuerySetManager):
    """
    Custom manager that will return only active users
    """

    def get_queryset(self) -> "QuerySetManager":
        queryset = super().get_queryset().filter(is_active=False)
        return queryset


class User(mongoz.Document):
    # Add the new manager
    inactives: ClassVar[QuerySetManager] = InactiveManager()
