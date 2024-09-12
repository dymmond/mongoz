# Fields

Fields are what is used within the [document](./documents.md) declaration (data types) and defines
wich types are going to be generated in the database.

Mongoz document declaration with typing is merely visual. The validations of the fields are not done by the typing of
the attribute of the documents but from the mongoz fields.

Rest assured that all the validations are done via Pydantic validation as usual, nothing changes.

## Data types

As **Mongoz** is a new approach on the top of Pydantic, the following keyword arguments are
supported in **all field types**.

* **default** - A value or a callable (function).
* **index** - A boolean. Determine if a database index should be created.
* **unique** - A boolean. Determines a unique constraint.

All the fields are required unless on the the following is set:

* **null** - A boolean. Determine if a column allows null.

    <sup>Set default to `None`</sup>

All the values you can pass in any Pydantic [Field](https://docs.pydantic.dev/latest/concepts/fields/)
are also 100% allowed within Mongoz fields.

### Importing fields

You have a few ways of doing this and those are the following:

```python
import mongoz
```

From `mongoz` you can access all the available fields.

```python
from mongoz.core.db import fields
```

From `fields` you should be able to access the fields directly.

```python
from mongoz.core.db.fields import Integer
```

You can import directly the desired field.

All the fields have specific parameters beisdes the ones [mentioned in data types](#data-types).


#### ObjectId

This is a special field that extends the `bson.ObjectId` directly and adds some Pydantic typing
to make sure it can still be serialized properly.

```python
import mongoz


class MyDocument(mongoz.Document):
    an_id: ObjectId = mongoz.ObjectId()
```

#### NullableObjectId

This is another special field that extends the `bson.ObjectId` and on the contrary of the [ObjectId](#objectid),
this one allows to specify null fields and not null as it derives from the mongoz core FieldFactory.

If defaults to `null=True` and it can be specified to `null=False` if required.

**Default**

```python
import mongoz


class MyDocument(mongoz.Document):
    an_id: ObjectId = mongoz.NullableObjectId()
```

**Null False**

```python
import mongoz


class MyDocument(mongoz.Document):
    an_id: ObjectId = mongoz.NullableObjectId(null=False)
```

#### String

```python
import mongoz


class MyDocument(mongoz.Document):
    description: str = mongoz.String(max_length=255)
    title: str = mongoz.String(max_length=50, min_length=200)
    ...

```

##### Parameters:

* **max_length** - An integer indicating the total length of string.
* **min_length** - An integer indicating the minimum length of string.

#### Integer

```python
import mongoz


class MyDocument(mongoz.Document):
    a_number: int = mongoz.Integer(default=0)
    another_number: int = mongoz.Integer(minimum=10)

```

#### Double

```python
import mongoz


class MyDocument(mongoz.Document):
    price: float = mongoz.Double(null=True)

```

Derives from the same as [Integer](#integer) and validates the decimal float.

##### Parameters:

* **minimum** - An integer, float or decimal indicating the minimum.
* **maximum** - An integer, float or decimal indicating the maximum.
* **max_digits** - Maximum digits allowed.
* **multiple_of** - An integer, float or decimal indicating the multiple of.
* **decimal_places** - The total decimal places.

#### Decimal

```python
import decimal
import mongoz

class MyDocument(mongoz.Document):
    price: decimal.Decimal = mongoz.Decimal(max_digits=5, decimal_places=2, null=True)

```

This operation will return the `bson.Decimal128` type which can be cast as string, float of any
normal type including `to_decimal()` to cast as a native `decimal.Decimal` field.

##### Parameters

* **minimum** - An integer indicating the minimum.
* **maximum** - An integer indicating the maximum.
* **max_digits** - An integer indicating the total maximum digits.
* **decimal_places** - An integer indicating the total decimal places.
* **multiple_of** - An integer, float or decimal indicating the multiple of.

#### Boolean

```python
import mongoz


class MyDocument(mongoz.Document):
    is_active: bool = mongoz.Boolean(default=True)
    is_completed: bool = mongoz.Boolean(default=False)
```

#### DateTime

```python
import datetime
import mongoz


class MyDocument(mongoz.Document):
    created_at: datetime.datetime = mongoz.DateTime(default=datetime.datetime.now)
```

##### Parameters

* **auto_now** - A boolean indicating the `auto_now` enabled.
* **auto_now_add** - A boolean indicating the `auto_now_add` enabled.


#### Date

```python
import datetime
import mongoz


class MyDocument(mongoz.Document):
    created_at: datetime.date = mongoz.Date(default=datetime.date.today)
    ...

```

##### Parameters

* **auto_now** - A boolean indicating the `auto_now` enabled.
* **auto_now_add** - A boolean indicating the `auto_now_add` enabled.

#### Time

```python
import datetime
import mongoz


def get_time():
    return datetime.datetime.now().time()


class MyDocument(mongoz.Document):
    time: datetime.time = mongoz.Time(default=get_time)
```

#### Object

```python
from typing import Dict, Any
import mongoz


class MyDocument(mongoz.Document):
    data: Dict[str, Any] = mongoz.Object(default={})

```

An object representation to be stored, for instance a `JSON`.

#### UUID

```python
from uuid import UUID
import mongoz


class MyDocument(mongoz.Document):
    uuid: UUID = fields.UUID()
```

Derives from the same as [String](#string) and validates the value of an UUID.

#### Array

This is a special Mongoz field that declares and defines an `Array` (list) of a given type.
For example, if you want to store a list of strings or any other type **but not mixed**.

```python
import mongoz


class MyDocument(mongoz.Document):
    tags: List[str] = fields.Array(str)
```

This can be particularly useful if you want to specify exactly which type you want to store and
nothig else.

##### Parameters

* **type_of** - The specific type to store, example `str`.

#### ArrayList

This is another special Mongoz field that declares and defines an `ArrayList` (list) of any type.
For example, if you want to store a list of strings, integers or any other type and **it can be mixed**.

```python
import mongoz


class MyDocument(mongoz.Document):
    tags: List[Union[str, int, float]] = fields.ArrayList()
```

This can be particularly useful if you want to specify exactly which type you want to store and
nothig else.

#### Embed

This is the field where the [EmbeddedDocuments](./embedded-documents.md) are declared.

```python
import mongoz

class Award(mongoz.EmbeddedDocument):
    name: str = mongoz.String()


class MyDocument(mongoz.Document):
    award: Award = fields.Embed(Award)
```

##### Parameters

* **document** - The specific embedded document type. If the `document` is not of the type
`mongoz.EmbeddedDocument`, a `FieldDefinitionError` is raised.
