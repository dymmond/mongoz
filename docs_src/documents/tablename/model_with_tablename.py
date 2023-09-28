import mongoz

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


class User(mongoz.Document):
    name: str = mongoz.String(max_length=255)
    age: int = mongoz.Integer()
    is_active: bool = mongoz.Boolean(default=True)

    class Meta:
        registry = registry
        tablename = "users"
        database = "my_db"
