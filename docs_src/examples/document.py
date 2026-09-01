import asyncio

from mongoz import Document, Registry, String

registry = Registry("mongodb://localhost:27017")


class User(Document):
    name: str = String(min_length=1)

    class Meta:
        registry = registry
        database = "docs"


async def main() -> None:
    async with registry:
        assert User.meta.collection.name == "users"


asyncio.run(main())
