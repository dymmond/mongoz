# Registry

When using the **Mongoz**, you must use the **Registry** object to tell exactly where the
database is going to be.

Imagine the registry as a mapping between your documents and the database where is going to be written.

And is just that, nothing else and very simple but effective object.

The registry is also the object that you might want to use when generating migrations using
Alembic.

```python hl_lines="19"
{!> ../../../docs_src/registry/model.py !}
```

## Parameters

* **url** - The database URL to connect to.

    ```python
    from mongoz import Registry

    registry = Registry(url="mongodb://localhost:27017")
    ```

## Client lifecycle

Each `Registry` constructs and owns exactly one PyMongo `AsyncMongoClient`. Database and collection
objects obtained from the registry reuse that client. A Registry becomes bound to the event loop of
its first database operation and must not be shared with another loop.

Close the Registry during application shutdown. `close()` is async and idempotent, but closing is
final: a closed Registry does not create a replacement client and cannot be reopened.

```python
registry = Registry(url="mongodb://localhost:27017")

try:
    database = registry.get_database("my_db")
    await database._db.command("ping")
finally:
    await registry.close()
```

For bounded work, use the async context manager:

```python
async with Registry(url="mongodb://localhost:27017") as registry:
    database = registry.get_database("my_db")
    await database._db.command("ping")
```

`registry.driver` exposes the registry-owned native PyMongo `AsyncMongoClient`. Its lifecycle still
belongs to the Registry; use `registry.close()` for cleanup.

## Sessions and transactions

PyMongo remains the owner of session and transaction lifecycle. Start a session from
`registry.driver`, then bind it to an isolated manager or queryset with `using_session()`. The bound
session is propagated to reads, creates, updates, deletes, counts, and distinct queries. Instance
writes accept the same session explicitly through `create(session=...)`,
`save(session=...)`, `update(session=...)`, and `delete(session=...)`. Index inspection/execution,
aggregation, and collection bulk writes also accept `session=` where PyMongo supports it.

```python
async with registry.driver.start_session() as session:
    async with await session.start_transaction():
        user = await User.objects.using_session(session).create(name="Mongoz")
        await user.update(name="MongoZ", session=session)
```

The transaction context commits on normal exit and aborts on exceptions. You can also call
`await session.abort_transaction()` explicitly. Native errors such as `DuplicateKeyError`, write
concern failures, and transaction errors are not translated; an exception leaving the transaction
context aborts its writes and the session context performs cleanup. A Registry remains reusable
after either commit or abort.

A PyMongo session is sequential and must not be used concurrently by multiple tasks. Mongoz does
not create an ambient or implicit session; every operation that belongs to the transaction must use
the session-bound query or pass the session to the document operation. Do not use `asyncio.gather()`
or create parallel tasks with one session. Use separate sequential sessions/transactions instead.

## Custom registry

Can you have your own custom Registry? Yes, of course! You simply need to subclass the `Registry`
class and continue from there like any other python class.

```python
{!> ../../../docs_src/registry/custom_registry.py !}
```

## Run some document checks

Sometimes you might want to make sure that all the documents have the indexes up to date beforehand. This
can be particularly useful if you already have a document and some indexes or were updated, added or removed. This
functionality runs those checks for all the documents of the given registry.

```python
{!> ../../../docs_src/registry/document_checks.py !}
```

### Using within a framework

This functionality can be useful to be also plugged if you use, for example, an ASGI Framework such as Starlette,
[Lilya](https://lilya.dev) or [Esmerald](https://esmerald.dev).

These frameworks handle the event lifecycle for you and this is where you want to make sure these checks are run beforehand.
The same application lifecycle should close the Registry on shutdown.

Since Mongoz is from the same team as [Lilya](https://lilya.dev) and [Esmerald](https://esmerald.dev), let us see how it
would look like with Esmerald.

```python
{!> ../../../docs_src/registry/asgi_fw.py !}
```
