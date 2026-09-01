import asyncio

from mongoz import Boolean, Document, Registry, String

registry = Registry("mongodb://localhost:27017")


class User(Document):
    name: str = String()
    active: bool = Boolean(default=True)

    class Meta:
        registry = registry
        database = "docs"


base = User.objects.filter(active=True)
named = base.filter(name__startswith="A")

assert base is not named
assert len(base._filter) == 1
assert len(named._filter) == 2

asyncio.run(registry.close())
