registry = Registry("mongodb://localhost:27017")

try:
    await registry.driver.admin.command("ping")
    await registry.document_checks()
finally:
    await registry.close()
