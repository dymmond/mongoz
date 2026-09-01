from __future__ import annotations

import os
from typing import cast

from pydantic import ValidationError
from pydantic_settings import SettingsError

from mongoz.conf.functional import LazyObject, empty
from mongoz.conf.global_settings import MongozSettings
from mongoz.conf.module_import import import_string
from mongoz.exceptions import ImproperlyConfigured

ENVIRONMENT_VARIABLE = "MONGOZ_SETTINGS_MODULE"


class MongozLazySettings(LazyObject):
    """
    A lazy proxy for either global Mongoz settings or a custom settings object.
    The user can manually configure settings prior to using them. Otherwise,
    Mongoz uses the settings module pointed to by MONGOZ_SETTINGS_MODULE.
    """

    def _setup(self, name: str | None = None) -> None:
        """
        Load the settings module pointed to by the environment variable. This
        is used the first time settings are needed, if the user hasn't
        configured settings manually.
        """
        settings_module: str = os.environ.get(
            ENVIRONMENT_VARIABLE, "mongoz.conf.global_settings.MongozSettings"
        )

        try:
            settings_class = import_string(settings_module)
        except (ImportError, AttributeError) as exc:
            raise ImproperlyConfigured(
                f"Could not import settings class {settings_module!r}: {exc}"
            ) from exc

        if not isinstance(settings_class, type) or not issubclass(settings_class, MongozSettings):
            raise ImproperlyConfigured(
                f"Settings class {settings_module!r} must inherit from MongozSettings."
            )

        try:
            configured_settings = settings_class()
        except ValidationError as exc:
            raise ImproperlyConfigured(
                f"Could not configure settings class {settings_module!r}."
            ) from exc
        except (SettingsError, TypeError):
            raise ImproperlyConfigured(
                f"Could not configure settings class {settings_module!r}."
            ) from None

        for setting in configured_settings.model_dump():
            if not setting.islower():
                raise ImproperlyConfigured(f"Setting {setting!r} must be lowercase.")

        self._wrapped = configured_settings

    def __repr__(self: MongozLazySettings) -> str:
        # Hardcode the class name as otherwise it yields 'MongozSettings'.
        if self._wrapped is empty:
            return "<MongozLazySettings [Unevaluated]>"
        return f'<MongozLazySettings "{self._wrapped.__class__.__name__}">'

    def __str__(self: MongozLazySettings) -> str:
        """Render settings without exposing values held by the wrapped model."""
        return self.__repr__()

    @property
    def configured(self) -> bool:
        """Return True if the settings have already been configured."""
        return self._wrapped is not empty


settings = cast("MongozSettings", MongozLazySettings())
