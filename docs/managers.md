# Managers

The managers are a great tool that **Mongoz** offers. Heavily inspired by [Edgy](https://edgy.tarsild.io), the managers
allow you to build unique tailored queries ready to be used by your documents.

**Mongoz** by default uses the the manager called `objects` which it makes it simple to understand.

Let us see an example.

```python
{!> ../docs_src/managers/simple.py !}
```

When querying the `User` table, the `objects` (manager) is the default and **should** be always
presented when doing it so.

!!! Danger
    This is only applied to the `manager` side of Mongoz, for example, when using
    `Document.objects....`. **When using `Document.query...` it will not work**.

### Custom manager

It is also possible to have your own custom managers and to do it so, you **should inherit**
the **QuerySetManager** class and override the `get_queryset()`.

For those familiar with Django managers, the principle is exactly the same. 😀

**The managers must be type annotated ClassVar** or an error be raised.

```python
{!> ../docs_src/managers/example.py !}
```

Let us now create new manager and use it with our previous example.

```python
{!> ../docs_src/managers/custom.py !}
```

These managers can be as complex as you like with as many filters as you desire. What you need is
simply override the `get_queryset()` and add it to your documents.

### Override the default manager

Overriding the default manager is also possible by creating the custom manager and overriding
the `objects` manager.

```python
{!> ../docs_src/managers/override.py !}
```

!!! Warning
    Be careful when overriding the default manager as you might not get all the results from the
    `.all()` if you don't filter properly.
