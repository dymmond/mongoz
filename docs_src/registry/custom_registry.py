import asyncio

import mongoz

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


class MyRegistry(mongoz.Registry):
    """
    Add logic unique to your registry or override
    existing functionality.
    """

    ...


models = MyRegistry(database_uri)


class User(mongoz.Document):
    """
    The User document to be created in the database as a table
    If no name is provided the in Meta class, it will generate
    a "users" table for you.
    """

    is_active: bool = mongoz.Boolean(default=False)

    class Meta:
        registry = registry
        database = "my_db"
