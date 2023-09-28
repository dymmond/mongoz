import mongoz

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


class User(mongoz.Document):
    """
    If the `tablename` is not declared in the `Meta`,
    edgy will pluralise the class name.

    This table will be called in the database `users`.
    """

    name: str = mongoz.String(max_length=255)
    age: int = mongoz.Integer()
    is_active: bool = mongoz.Boolean(default=True)

    class Meta:
        registry = registry
        database = "my_db"
