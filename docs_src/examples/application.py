# Pseudocode: adapt these names to the lifecycle API of the chosen ASGI framework.
registry = Registry(settings.mongodb_uri)

app.on_startup(registry.document_checks)
app.on_shutdown(registry.close)
