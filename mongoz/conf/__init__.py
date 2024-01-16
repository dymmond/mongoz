import os

if not os.environ.get("SETTINGS_MODULE"):
    os.environ.setdefault("SETTINGS_MODULE", "mongoz.conf.global_settings.MongozSettings")

from dymmond_settings import settings as settings
