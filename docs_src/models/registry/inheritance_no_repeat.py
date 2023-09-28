import mongoz

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


class BaseDocument(mongoz.Document):
    """
    The base document for all documents using the `registry` registry.
    """

    class Meta:
        abstract = True
        registry = registry


class User(BaseDocument):
    name: str = mongoz.String(max_length=255)
    is_active: bool = mongoz.Boolean(default=True)


class Product(BaseDocument):
    sku: str = mongoz.String(max_length=255, null=False)
