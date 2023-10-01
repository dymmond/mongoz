# MongoZ

<p align="center">
  <a href="https://mongoz.tarsild.io"><img src="https://res.cloudinary.com/tarsild/image/upload/v1695724284/packages/mongoz/nwtcudxmncgoyw4em0th.png" alt='mongoz'></a>
</p>

<p align="center">
    <em>🔥 ODM with Pydantic made it simple 🔥</em>
</p>

<p align="center">
<a href="https://github.com/tarsil/mongoz/workflows/Test%20Suite/badge.svg?event=push&branch=main" target="_blank">
    <img src="https://github.com/tarsil/mongoz/workflows/Test%20Suite/badge.svg?event=push&branch=main" alt="Test Suite">
</a>

<a href="https://pypi.org/project/mongoz" target="_blank">
    <img src="https://img.shields.io/pypi/v/mongoz?color=%2334D058&label=pypi%20package" alt="Package version">
</a>

<a href="https://pypi.org/project/mongoz" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/mongoz.svg?color=%2334D058" alt="Supported Python versions">
</a>
</p>

---

**Documentation**: [https://mongoz.tarsild.io][mongoz] 📚

**Source Code**: [https://github.com/tarsil/mongoz](https://github.com/tarsil/mongoz)

---

## Motivation

MongoZ is an async Python ODM (Object Document Mapper) for MongoDB built on top of [Motor][motor] and
[Pydantic][pydantic].

MongoZ is also inspired by the great work of [Aminalee](https://aminalaee.dev/mongox/) from the
MongoX.

So why a MongoZ if there is a MongoX? Well, MongoZ is from the same author of [Esmerald][esmerald],
[Saffier][saffier], [Mongoz][mongoz] and many other tools out there and they all follow a specific need
and pattern of development.

Mongox implements really well some operations with MongoDB but for use cases where [Signals](https://mongoz.tarsild.io/sinals.md),
for example, are needed, Mongox was not aiming at it and also since the creator of Mongoz is the
same as [Saffier][saffier] and [Saffier][saffier], the friendly interface to interact is also a must.

In the end, there was a need to add Pydantic 2+ with some more extras that was not coming in the
Mongox.

## Mongoz

This is some sort of a fork of Mongox with a rewritten core but reusing some of its best features
while adding additional ones and a common and friendly interface as well as intuitive.

This ODM is designed for **async** which means flexibility and compatibility with various frameworks
out there such as [Esmerald][esmerald], FastAPI, Sanic, Starlette and many others making MongoZ
**framework agnostic**.

## Features

While adopting a familiar interface, it offers some cool and powerful features using Pydantic and
Motor.

### Syntax

**Mongoz allows two different types of syntax to be used**.

* With a familiar interface inspired by Django.
* With a familiar interface inspired by Mongox.

**The documentation follows a more familiar interface inspired by [Edgy][edgy] but will also show**
**how you could also use the other allowed syntax as well**

### Key features

* **Document inheritance** - For those cases where you don't want to repeat yourself while maintaining integrity of the documents.
* **Abstract classes** - That's right! Sometimes you simply want a document that holds common fields that doesn't need to created as
a document in the database.
* **Meta classes** - If you are familiar with Django, this is not new to you and Mongoz offers this in the same fashion.
* **Filters** - Filter by any field you want and need.
* **Model operators** - Classic operations such as `update`, `get`, `get_or_none` and many others.
* **Indexes** - Unique indexes through meta fields.
* **Signals** - Quite useful feature if you want to "listen" to what is happening with your documents.

And a lot more you can do here.

## Installation

To install Mongoz, run:

```shell
$ pip install mongoz
```

## Quickstart

The following is an example how to start with Mongoz and more details and examples can be found throughout the documentation.

Use `ipython` to run the following from the console, since it supports `await`.

```python
import asyncio

import mongoz

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri, event_loop=asyncio.get_running_loop)


class User(mongoz.Document):
    name: str = mongoz.String(max_length=255)
    email: str = mongoz.Email(max_length=255)
    is_verified: bool = mongoz.Boolean(default=False)

    class Meta:
        registry = registry
        database = "my_db"
```

Now you can generate some documents and insert them into the database.

=== "Simple"

    ```python
    user = await User.objects.create(name="Mongoz", email="mongoz@mongoz.com")
    ```

=== "Alternative"

    ```python
    user = await User(name="Mongoz", email="mongoz@mongoz.com").create()
    ```

This will return an instance of a `User` in a Pydantic model and `mypy` will understand this is a
`User` instance automatically which meand the type hints and validations will work everywhere.

### Fetching

Since Mongoz was built on the top of Motor, means you can also use the same pattern to query as used
in PyMongo/Motor.

=== "Simple"

    ```python
    user = await User.objects.get(name="Mongoz")
    ```

=== "Alternative"

    ```python
    user = await User.query({"name": "Mongoz"}).get()
    ```

Or you can use the `User` fields instead of dictionaries (check the "Alternative" for this option).

=== "Simple"

    ```python
    user = await User.objects.get(name="Mongoz")
    ```

=== "Alternative"

    ```python
    user = await User.query({User.name: "Mongoz"}).get()
    ```

Or a more python similar approach (check the "Alternative" for this option).

=== "Simple"

    ```python
    user = await User.objects.get(name="Mongoz")
    ```

=== "Alternative"

    ```python
    user = await User.query(User.name == "Mongoz").get()
    ```

There are plenty of operations you can do with Mongoz and you can see them all throughout the
documentation or in the [Queries](./queries.md) section.

**Mongoz** praises simplicity and there is no preference in the syntax used within the queries.
You can use what we called "Mongoz" option and the "Alternative" at the same time as both work
really well combined.

**Both are Mongoz syntaxes but for the sake of the documentation, we classify them with different names for representation purposes only**.

## Note

Mongoz document declaration with typing is merely visual. The validations of the fields are not done by the typing of
the attribute of the documents but from the mongoz fields.

Which means you don't need to worry about the wrong typing as long as you declare the correct field type.

So does that mean Pydantic won't work if you don't declare the type? Absolutely not.
Internally Mongoz runs those validations through the declared fields and the Pydantic validations
are done exactly in the same way you do a normal Pydantic model.

Nothing to worry about!


[mongoz]: https://mongoz.tarsild.io
[motor]: https://github.com/mongodb/motor
[pydantic]: https://pydantic.dev/
[mongoz]: https://mongoz.tarsild.io
[saffier]: https://saffier.tarsild.io
[edgy]: https://edgy.tarsild.io
[esmerald]: https://esmerald.dev
