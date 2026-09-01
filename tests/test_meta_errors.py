from typing import ClassVar, List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, ObjectId
from mongoz.core.db.querysets.core.manager import Manager
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


async def test_abstract_custom_manager_does_not_count_inherited_objects() -> None:
    class AbstractRecord(Document):
        custom: ClassVar[Manager] = Manager()

        class Meta:
            abstract = True
            registry = client
            database = "test_db"

    assert isinstance(AbstractRecord.custom, Manager)


async def test_abstract_document_rejects_two_declared_managers() -> None:
    with pytest.raises(ImproperlyConfigured, match="Multiple managers"):

        class InvalidAbstractRecord(Document):
            first: ClassVar[Manager] = Manager()
            second: ClassVar[Manager] = Manager()

            class Meta:
                abstract = True
                registry = client
                database = "test_db"
