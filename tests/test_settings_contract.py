import traceback
from collections.abc import AsyncGenerator

import pytest
from pydantic import SecretStr, ValidationError, field_validator

from mongoz.conf import ENVIRONMENT_VARIABLE, MongozLazySettings
from mongoz.conf.global_settings import MongozSettings
from mongoz.exceptions import ImproperlyConfigured

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
async def test_database() -> AsyncGenerator[None, None]:
    """Override shared database setup because these pure tests perform no MongoDB I/O."""
    yield


class MissingValueSettings(MongozSettings):
    required_value: str


class RejectingSecretSettings(MongozSettings):
    api_token: SecretStr

    @field_validator("api_token")
    @classmethod
    def reject_token(cls, value: SecretStr) -> SecretStr:
        raise ValueError("token was rejected")


class ListSettings(MongozSettings):
    values: list[int]


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


async def test_invalid_settings_do_not_render_secret_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = "manifest-secret-value"
    monkeypatch.setenv(
        ENVIRONMENT_VARIABLE, "tests.test_settings_contract.RejectingSecretSettings"
    )
    monkeypatch.setenv("API_TOKEN", marker)

    with pytest.raises(ImproperlyConfigured) as raised:
        MongozLazySettings()._setup()

    rendered = "".join(
        traceback.format_exception(type(raised.value), raised.value, raised.value.__traceback__)
    )
    assert marker not in str(raised.value)
    assert marker not in str(raised.value.__cause__)
    assert marker not in rendered


async def test_lazy_settings_string_rendering_never_exposes_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = "plain-value-that-must-not-be-rendered"
    monkeypatch.setenv(ENVIRONMENT_VARIABLE, "tests.test_settings_contract.MissingValueSettings")
    monkeypatch.setenv("REQUIRED_VALUE", marker)
    lazy_settings = MongozLazySettings()
    lazy_settings._setup()

    assert marker not in str(lazy_settings)
    assert str(lazy_settings) == repr(lazy_settings)


async def test_settings_source_errors_use_the_public_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENVIRONMENT_VARIABLE, "tests.test_settings_contract.ListSettings")
    monkeypatch.setenv("VALUES", "not-json")

    with pytest.raises(ImproperlyConfigured, match="Could not configure") as raised:
        MongozLazySettings()._setup()

    assert raised.value.__cause__ is None
