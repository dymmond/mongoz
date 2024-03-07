import os

os.environ.setdefault("OVERRIDE_SETTINGS_MODULE_VARIABLE", "MONGOZ_SETTINGS_MODULE")

if not os.environ.get("MONGOZ_SETTINGS_MODULE"):
    os.environ.setdefault("MONGOZ_SETTINGS_MODULE", "mongoz.conf.global_settings.MongozSettings")

from dymmond_settings import settings as settings  # noqa
