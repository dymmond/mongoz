from typing import List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, ObjectId
from mongoz.exceptions import ImproperlyConfigured
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


async def test_improperly_configured_for_missing_database():
    with pytest.raises(ImproperlyConfigured) as raised:

        class Movie(Document):
            name: str = mongoz.String()
            year: int = mongoz.Integer()
            tags: Optional[List[str]] = mongoz.Array(str, null=True)
            uuid: Optional[ObjectId] = mongoz.UUID(null=True)
            is_published: bool = mongoz.Boolean(default=False)

            class Meta:
                registry = client

    assert (
        raised.value.args[0]
        == "'database' for the table not found in the Meta class or any of the superclasses. You must set the database in the Meta."
    )
