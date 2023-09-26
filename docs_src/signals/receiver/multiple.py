import asyncio

import mongoz

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri, event_loop=asyncio.get_running_loop)


class User(mongoz.Document):
    name = mongoz.String(max_length=255)
    email = mongoz.Email(max_length=255)
    is_verified = mongoz.Boolean(default=False)

    class Meta:
        registry = registry
        database = "my_db"


class Profile(mongoz.Document):
    profile_type = mongoz.String(max_length=255)

    class Meta:
        registry = registry
        database = "my_db"
