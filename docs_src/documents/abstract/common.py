import uuid

import mongoz

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


class BaseDocument(mongoz.Document):
    name: str = mongoz.String(max_length=255)

    class Meta:
        abstract = True
        registry = registry
        database = "my_db"

    def get_description(self):
        """
        Returns the description of a record
        """
        return getattr(self, "description", None)


class User(BaseDocument):
    """
    Inheriting the fields from the abstract class
    as well as the Meta data.
    """

    phone_number: str = mongoz.String(max_length=15)
    description: str = mongoz.String()

    def transform_phone_number(self):
        # logic here for the phone number
        ...


class Product(BaseDocument):
    """
    Inheriting the fields from the abstract class
    as well as the Meta data.
    """

    sku: str = mongoz.String(max_length=255)
    description: str = mongoz.String()

    def get_sku(self):
        # Logic to obtain the SKU
        ...
