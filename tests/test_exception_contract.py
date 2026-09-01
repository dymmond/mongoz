from collections.abc import AsyncGenerator

import pytest

import mongoz
from mongoz.exceptions import (
    AbstractDocumentError,
    DocumentNotFound,
    FieldDefinitionError,
    ImproperlyConfigured,
    IndexError as MongozIndexError,
    InvalidKeyError,
    InvalidObjectIdError,
    MongozException,
    MultipleDocumentsReturned,
    OperatorInvalid,
    SignalError,
)

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
async def test_database() -> AsyncGenerator[None, None]:
    """Keep pure exception contract tests independent from MongoDB availability."""
    yield


async def test_exception_messages_preserve_and_separate_all_context() -> None:
    error = FieldDefinitionError("field", 0, detail="is invalid")

    assert error.args == ("field", "0", "is invalid")
    assert error.detail == "is invalid"
    assert str(error) == "field 0 is invalid"
    assert repr(error) == "FieldDefinitionError('field 0 is invalid')"


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (DocumentNotFound(), "Document not found."),
        (MultipleDocumentsReturned(), "Multiple documents returned."),
    ],
)
async def test_query_cardinality_errors_have_useful_default_messages(
    error: MongozException, message: str
) -> None:
    assert str(error) == message


async def test_public_exception_taxonomy_is_small_and_consistent() -> None:
    exception_types = (
        AbstractDocumentError,
        DocumentNotFound,
        FieldDefinitionError,
        ImproperlyConfigured,
        MongozIndexError,
        InvalidKeyError,
        InvalidObjectIdError,
        MultipleDocumentsReturned,
        OperatorInvalid,
        SignalError,
    )

    assert all(issubclass(error_type, MongozException) for error_type in exception_types)


async def test_all_public_exceptions_are_exported_from_top_level_package() -> None:
    expected = {
        "AbstractDocumentError",
        "DocumentNotFound",
        "FieldDefinitionError",
        "ImproperlyConfigured",
        "IndexError",
        "InvalidKeyError",
        "InvalidObjectIdError",
        "MongozException",
        "MultipleDocumentsReturned",
        "OperatorInvalid",
        "SignalError",
    }

    assert expected <= set(mongoz.__all__)
    assert all(getattr(mongoz, name) is not None for name in expected)
