# Registry

When using the **Mongoz**, you must use the **Registry** object to tell exactly where the
database is going to be.

Imagine the registry as a mapping between your documents and the database where is going to be written.

And is just that, nothing else and very simple but effective object.

The registry is also the object that you might want to use when generating migrations using
Alembic.

```python hl_lines="19"
{!> ../docs_src/registry/model.py !}
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
{!> ../docs_src/registry/custom_registry.py !}
```
