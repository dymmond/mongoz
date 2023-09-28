import mongoz
from mongoz import Index

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


class User(mongoz.Model):
    name: str = mongoz.String(max_length=255)
    age: int = mongoz.Integer()
    email: str = mongoz.Email(max_length=70)
    is_active: bool = mongoz.Boolean(default=True)
    status: str = mongoz.String(max_length=255)

    class Meta:
        registry = registry
        indexes = [Index("name", unique=True)]
