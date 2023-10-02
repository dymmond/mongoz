from datetime import datetime

from my_project.utils import get_db_connection

import mongoz

registry = get_db_connection()


class BaseDocument(mongoz.Document):
    class Meta:
        abstract = True
        registry = registry
        database = "my_db"


class User(BaseDocument):
    """
    Base document for a user
    """

    first_name: str = mongoz.String(max_length=150)
    last_name: str = mongoz.String(max_length=150)
    username: str = mongoz.String(max_length=150, unique=True)
    email: str = mongoz.Email(max_length=120, unique=True)
    password: str = mongoz.String(max_length=128)
    last_login: datetime = mongoz.DateTime(null=True)
    is_active: bool = mongoz.Boolean(default=True)
    is_staff: bool = mongoz.Boolean(default=False)
    is_superuser: bool = mongoz.Boolean(default=False)
