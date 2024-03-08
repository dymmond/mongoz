from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from mongoz.conf.functional import LazyObject, empty
from mongoz.conf.module_import import import_string

if TYPE_CHECKING:
    from mongoz.conf.global_settings import MongozSettings

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

        settings: type[MongozSettings] = import_string(settings_module)

        for setting, _ in settings().dict().items():
            assert setting.islower(), "%s should be in lowercase." % setting

        self._wrapped = settings()

    def __repr__(self: MongozLazySettings) -> str:
        # Hardcode the class name as otherwise it yields 'MongozSettings'.
        if self._wrapped is empty:
            return "<MongozLazySettings [Unevaluated]>"
        return f'<MongozLazySettings "{self._wrapped.__class__.__name__}">'

    @property
    def configured(self) -> Any:
        """Return True if the settings have already been configured."""
        return self._wrapped is not empty


settings: type[MongozSettings] = MongozLazySettings()  # type: ignore
