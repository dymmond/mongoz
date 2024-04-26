import mongoz

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


class User(mongoz.Document):
    name: str = mongoz.String(max_length=255)
    email: str = mongoz.String(max_length=70)
    is_active: bool = mongoz.Boolean(default=True)

    class Meta:
        registry = registry
        database = "my_db"


await User.objects.create(name="Mongoz", email="foo@bar.com")  # noqa

user = await User.objects.get(name="Mongoz")  # noqa
# User(id=ObjectId(...))
