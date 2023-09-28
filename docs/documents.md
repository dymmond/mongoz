# Documents

As you are probably aware, MongoDB is a NoSQL database, which means it doesn't have tables but
**documents** instead.

This also means that with documents and NoSQL, **there are no joins and foreign keys**.

**Mongoz** implements those documents in a more friendly interface if you are still familiar with
ORMs or even if you use something like [Mongoz][edgy]. No reason to overcomplicate, right?

## Declaring documents

When declaring documents by simply inheriting from `mongoz.Document` object and define the attributes
using the mongoz [Fields](./fields.md).

For each document defined you also need to set **one** mandatory field, the `registry` which is also
an instance of `Registry` from Mongoz.

There are more parameters you can use and pass into the document such as [tablename](#metaclass) and
a few more but more on this in this document.

Since **Mongoz** took inspiration from the interface of [Mongoz][edgy], that also means that a [Meta](#the-meta-class)
class should be declared.

Although this looks very simple, in fact **Mongoz** is doing a lot of work for you behind the
scenes.

```python
{!> ../docs_src/documents/declaring_models.py !}
```

## The Meta class

When declaring a document, it is **crucial** having the `Meta` class declared. There is where you
declare the `metadata` needed for your documents.

Currently the available parameters for the meta are:

* **registry** - The [registry](./registry.md) instance for where the document will be generated. This
field is **mandatory** and it will raise an `ImproperlyConfigured` error if no registry is found.

* **tablename** - The name of the table in the database, **not the class name**.

    <sup>Default: `name of class pluralised`<sup>

* **database** - The name of the database where the document will be created.
* **abstract** - If the document is abstract or not. If is abstract, then it won't generate the
database table.

    <sup>Default: `False`<sup>

* **indexes** - The extra custom indexes you want to add to the document.

### Registry

Working with a [registry](./registry.md) is what makes **Mongoz** dynamic and very flexible with
the familiar interface we all love. Without the registry, the document doesn't know where it should
get the data from.

Imagine a `registry` like a bridge because it does exactly that.

Let us see some examples in how to use the registry with simple design and with some more complex
approaches.

#### In a nutshell

```python
{!> ../docs_src/documents/registry/nutshell.py !}
```

As you can see, when declaring the `registry` and assigning it to `registry`, that same `registry` is
then used in the `Meta` of the document.

#### With inheritance

Yes, you can also use the document inheritance to help you out with your documents and avoid repetition.

```python
{!> ../docs_src/documents/registry/inheritance_no_repeat.py !}
```

As you can see, the `User` and `Product` tables are inheriting from the `BaseDocument` where the
`registry` was already declared. This way you can avoid repeating yourself over and over again.

The reason for the `abstract=True` it is because we do not want to create a document of that
specific class in the database.

This can be particularly useful if you have more than one `registry` in your system and you want
to split the bases by responsabilities.

#### With abstract classes

What if your class is abstract? Can you inherit the registry anyway?

Of course! That doesn't change anything with the registry.

```python
{!> ../docs_src/documents/registry/inheritance_abstract.py !}
```

### Table name

This is actually very simple and also comes with defaults. When creating a [document](#declaring-documents)
if a `tablename` field in the `Meta` object is not declared, it will pluralise the python class.

#### Document without table name

```python
{!> ../docs_src/documents/tablename/model_no_tablename.py !}
```

As mentioned in the example, because a `tablename` was not declared, **Mongoz** will pluralise
the python class name `User` and it will become `users` in your database.

#### Document with a table name

```python
{!> ../docs_src/documents/tablename/model_with_tablename.py !}
```

Here the `tablename` is being explicitly declared as `users`. Although it matches with a
puralisation of the python class name, this could also be something else.

```python
{!> ../docs_src/documents/tablename/model_diff_tn.py !}
```

In this example, the `User` class will be represented by a `db_users` mapping into the database.

!!! Tip
    Calling `tablename` with a different name than your class it doesn't change the behaviour
    in your codebase. You will still access the given table in your codebase via main class.

### Abstract

As the name suggests, it is when you want to declare an abstract document.

Why do you need an abstract document in the first place? Well, for the same reason when you need to
declare an abstract class in python but for this case you simply don't want to generate a table
from that document declaration.

This can be useful if you want to hold common functionality across documents and don't want to repeat
yourself.

The way of declaring an abstract document in **Mongoz** is by passing `True` to the `abstract`
attribute in the [meta](#the-meta-class) class.

#### In a nutshell

In this document we already mentioned abstract documents and how to use them but let us use some more
examples to be even clear.

```python
{!> ../docs_src/documents/abstract/simple.py !}
```

This document itself does not do much alone. This simply creates a `BaseDocument` and declares the
[registry](#registry) as well as declares the `abstract` as `True`.

#### Use abstract documents to hold common functionality

Taking advantage of the abstract documents to hold common functionality is usually the common use
case for these to be use in the first place.

Let us see a more complex example and how to use it.

```python
{!> ../docs_src/documents/abstract/common.py !}
```

This is already quite a complex example where `User` and `Product` have both common functionality
like the `id` and `description` as well the `get_description()` function.

### Indexes

Sometimes you might want to add specific designed indexes to your documents. Database indexes also
somes with costs and you **should always be careful** when creating one.

Mongoz provides an `Index` object that must be used when declaring documents indexes.

```python
from mongoz import Index, IndexType, Order
```
#### Parameters

The `Index` parameters are:

* **key** - A string name of the field (key) for the index.
* **keys** - List of python tuples (string, order) for the index.
* **name** - The index name.

The `Index` in Mongoz is an extension of the [`pymongo.IndexModel`](https://pymongo.readthedocs.io/en/stable/api/pymongo/operations.html#pymongo.operations.IndexModel.document).

#### Simple index

```python hl_lines="17"
{!> ../docs_src/documents/indexes/simple2.py !}
```

#### Complex indexes

```python hl_lines="17-20"
{!> ../docs_src/documents/indexes/complex_together.py !}
```

[edgy]: https://edgy.tarsild.io
