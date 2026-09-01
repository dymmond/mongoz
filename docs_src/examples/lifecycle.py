import asyncio

from mongoz import Document, Registry, String


async def main() -> None:
    registry = Registry("mongodb://localhost:27017")

    class HealthRecord(Document):
        status: str = String()

        class Meta:
            registry = registry
            database = "application"

    try:
        await registry.driver.admin.command("ping")
        await registry.document_checks()
    finally:
        await registry.close()


asyncio.run(main())
