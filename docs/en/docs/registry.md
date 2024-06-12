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

Since Mongoz is from the same team as [Lilya](https://lilya.dev) and [Esmerald](https://esmerald.dev), let us see how it
would look like with Esmerald.

```python
{!> ../../../docs_src/registry/asgi_fw.py !}
```
