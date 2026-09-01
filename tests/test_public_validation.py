import os
import subprocess
import sys
from collections.abc import AsyncGenerator, Callable

import pytest

import mongoz
from mongoz import Document, Q
from mongoz.conf.global_settings import MongozSettings
from mongoz.exceptions import FieldDefinitionError, InvalidKeyError, OperatorInvalid
from tests.conftest import client

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
async def test_database() -> AsyncGenerator[None, None]:
    """Keep public validation tests independent from MongoDB availability."""
    yield


class ValidationDocument(Document):
    name: str = mongoz.String()

    class Meta:
        registry = client
        database = "test_db"


class UppercaseSettings(MongozSettings):
    UPPERCASE_SETTING: str = "invalid"


@pytest.mark.parametrize(
    "operation",
    [
        lambda: ValidationDocument.query(True),
        lambda: ValidationDocument.query().query(True),
        lambda: ValidationDocument.objects.raw(True),
    ],
)
async def test_query_arguments_raise_stable_errors(operation: Callable[[], object]) -> None:
    with pytest.raises(FieldDefinitionError, match=r"bool"):
        operation()


async def test_sort_rejects_multiple_keyword_fields() -> None:
    with pytest.raises(FieldDefinitionError, match="one keyword field"):
        ValidationDocument.objects.sort(first=1, second=2)


async def test_query_operator_validation_is_not_assertion_based() -> None:
    with pytest.raises(OperatorInvalid, match=r"\$where.*string"):
        Q.where("name", 1)
    with pytest.raises(OperatorInvalid, match=r"\$gte.*boolean"):
        Q.gte("age", True)


async def test_unrelated_nested_field_access_has_context() -> None:
    assert hasattr(ValidationDocument.name, "__func__") is False
    with pytest.raises(InvalidKeyError, match=r"name.*missing"):
        _ = ValidationDocument.name.missing


async def test_public_validation_survives_optimized_python() -> None:
    source = """
import mongoz
from mongoz.exceptions import FieldDefinitionError, OperatorInvalid

registry = mongoz.Registry('mongodb://localhost:27017')

class Item(mongoz.Document):
    name: str = mongoz.String()

    class Meta:
        registry = registry
        database = 'optimized_validation'

checks = (
    (lambda: Item.query(True), FieldDefinitionError),
    (lambda: Item.query().query(True), FieldDefinitionError),
    (lambda: Item.objects.raw(True), FieldDefinitionError),
    (lambda: Item.objects.sort(first=1, second=2), FieldDefinitionError),
    (lambda: mongoz.Q.where('name', 1), OperatorInvalid),
    (lambda: mongoz.Q.gte('age', True), OperatorInvalid),
)

for operation, expected in checks:
    try:
        operation()
    except expected:
        pass
    else:
        raise RuntimeError(f'{expected.__name__} was disabled by optimization')
"""
    result = subprocess.run(
        [sys.executable, "-O", "-c", source],
        cwd=os.getcwd(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


async def test_settings_validation_survives_optimized_python() -> None:
    source = """
from mongoz.conf import settings
from mongoz.exceptions import ImproperlyConfigured

try:
    settings.UPPERCASE_SETTING
except ImproperlyConfigured as error:
    if 'UPPERCASE_SETTING' not in str(error):
        raise
else:
    raise RuntimeError('settings validation was disabled by optimization')
"""
    environment = os.environ.copy()
    environment["MONGOZ_SETTINGS_MODULE"] = "tests.test_public_validation.UppercaseSettings"
    result = subprocess.run(
        [sys.executable, "-O", "-c", source],
        cwd=os.getcwd(),
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
