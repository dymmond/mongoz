import mongoz
from mongoz import Database, Index, IndexType, Order, Registry

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


class User(mongoz.Model):
    name: str = mongoz.String(max_length=255, index=True, unique=True)
    age: int = mongoz.Integer()
    email: str = mongoz.Email(max_length=70)
    is_active: bool = mongoz.Boolean(default=True)
    status: str = mongoz.String(max_length=255)

    class Meta:
        registry = registry
        indexes = [
            Index(keys=[("age", Order.DESCENDING), ("email", IndexType.HASHED)]),
        ]
