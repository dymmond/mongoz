import warnings
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest

import mongoz
from mongoz import Document, EmbeddedDocument
from tests.conftest import client

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
async def test_database() -> AsyncGenerator[None, None]:
    """Override shared database setup because these pure tests perform no MongoDB I/O."""
    yield


class Award(EmbeddedDocument):
    name: str = mongoz.String()


class Crew(EmbeddedDocument):
    award: Award = mongoz.Embed(Award)


class TimestampedRecord(Document):
    created_at: datetime = mongoz.DateTime(auto_now=True)

    class Meta:
        registry = client
        database = "test_db"


async def test_embedded_validation_preserves_nested_model_instances() -> None:
    award = Award(name="Academy Award")

    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        crew = Crew(award=award)
        dumped = crew.model_dump()

    assert crew.award is award
    assert dumped == {"award": {"name": "Academy Award"}}


async def test_callable_document_defaults_are_resolved_before_serialization() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        record = TimestampedRecord()
        dumped = record.model_dump()

    assert isinstance(record.created_at, datetime)
    assert isinstance(dumped["created_at"], datetime)
