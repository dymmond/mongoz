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
    objects: ClassVar[QuerySetManager] = InactiveManager()

    name: str = mongoz.String(max_length=255)
    email: str = mongoz.Email(max_length=70)
    is_active: bool = mongoz.Boolean(default=True)


# Create an inactive user
await User.objects.create(name="Edgy", email="foo@bar.com", is_active=False)  # noqa

# You can also create a user using the new manager
await User.objects.create(name="Another Edgy", email="bar@foo.com", is_active=False)  # noqa

# Create a user using the default manager
await User.objects.create(name="Edgy", email="user@edgy.com")  # noqa

# Querying them all
user = await User.objects.all()  # noqa
# [User(ObjectId(...)), User(ObjectId(...))]
