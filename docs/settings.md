# Settings

Who never had that feeling that sometimes haing some database settings would be nice? Well, since
Mongoz is from the same author of [Esmerald][esmerald] and since [Esmerald][esmerald] is [settings][esmerald_settings] oriented, why not apply
the same principle but in a simpler manner but to Mongoz?

This is exactly what happened.

## Mongoz Settings Module

The way of using the settings object within a Mongoz use of the ORM is via:

* **MONGOZ_SETTINGS_MODULE** environment variable.

All the settings are **[Pydantic BaseSettings](https://pypi.org/project/pydantic-settings/)** objects which makes it easier to use and override
when needed.

### MONGOZ_SETTINGS_MODULE

Mongoz by default uses is looking for a `MONGOZ_SETTINGS_MODULE` environment variable to run and
apply the given settings to your instance.

If no `MONGOZ_SETTINGS_MODULE` is found, Mongoz then uses its own internal settings which are
widely applied across the system.

#### Custom settings

When creating your own custom settings class, you should inherit from `MongozSettings` which is
the class responsible for all internal settings of Mongoz and those can be extended and overriden
with ease.

Something like this:

```python title="myproject/configs/settings.py"
{!> ../docs_src/settings/custom_settings.py !}
```

Super simple right? Yes and that is the intention. Mongoz does not have a lot of settings but
has some which are used across the codebase and those can be overriden easily.

!!! Danger
    Be careful when overriding the settings as you might break functionality. It is your own risk
    doing it.



[esmerald_settings]: https://esmerald.dev/application/settings/
[esmerald]: https://esmerald.dev/
