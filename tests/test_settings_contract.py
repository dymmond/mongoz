from collections.abc import AsyncGenerator

import pytest
from pydantic import ValidationError

from mongoz.conf import ENVIRONMENT_VARIABLE, MongozLazySettings
from mongoz.conf.global_settings import MongozSettings
from mongoz.exceptions import ImproperlyConfigured

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
async def test_database() -> AsyncGenerator[None, None]:
    """Keep settings contract tests independent from MongoDB availability."""
    yield


class MissingValueSettings(MongozSettings):
    required_value: str


async def test_lazy_settings_use_defaults_without_eager_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ENVIRONMENT_VARIABLE, raising=False)
    lazy_settings = MongozLazySettings()

    assert lazy_settings.configured is False
    assert repr(lazy_settings) == "<MongozLazySettings [Unevaluated]>"

    assert "exact" in lazy_settings.operators
    assert lazy_settings.configured is True


@pytest.mark.parametrize(
    ("settings_path", "message"),
    [
        ("missing.module.Settings", "Could not import settings class"),
        ("builtins.str", "must inherit from MongozSettings"),
    ],
)
async def test_invalid_settings_imports_raise_configuration_errors(
    monkeypatch: pytest.MonkeyPatch, settings_path: str, message: str
) -> None:
    monkeypatch.setenv(ENVIRONMENT_VARIABLE, settings_path)

    with pytest.raises(ImproperlyConfigured, match=message):
        MongozLazySettings()._setup()


async def test_invalid_settings_values_preserve_their_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        ENVIRONMENT_VARIABLE,
        "tests.test_settings_contract.MissingValueSettings",
    )

    with pytest.raises(ImproperlyConfigured, match="Could not configure") as raised:
        MongozLazySettings()._setup()

    assert isinstance(raised.value.__cause__, ValidationError)
