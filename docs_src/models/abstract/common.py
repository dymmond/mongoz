import uuid

import mongoz

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


class BaseModel(mongoz.Model):
    id: uuid.UUID = mongoz.UUID(primary_key=True, default=uuid.uuid4)
    name: str = mongoz.String(max_length=255)

    class Meta:
        abstract = True
        registry = registry

    def get_description(self):
        """
        Returns the description of a record
        """
        return getattr(self, "description", None)


class User(BaseModel):
    """
    Inheriting the fields from the abstract class
    as well as the Meta data.
    """

    phone_number: str = mongoz.String(max_length=15)
    description: str = mongoz.String()

    def transform_phone_number(self):
        # logic here for the phone number
        ...


class Product(BaseModel):
    """
    Inheriting the fields from the abstract class
    as well as the Meta data.
    """

    sku: str = mongoz.String(max_length=255)
    description: str = mongoz.String()

    def get_sku(self):
        # Logic to obtain the SKU
        ...
