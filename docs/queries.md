# Queries

Making queries is a must when using an ODM and being able to make complex queries is even better
when allowed.

MongoDB is known for its performance when querying a database and it is very fast.

When making queries in a [document][document], the ODM allow two different possible ways of querying.
One is using its internal **manager** and the second its internal **queryset**.

In reality, the `manager` and `queryset` are very similar but for internal purposes it was decided
to call both in this way to be clear in the way the queries can be done.

If you haven't yet seen the [documents][document] section, now would be a great time to have a look
and get yourself acquainted .

For the purpose of this documentation, we will be showing how to query using both the `manager` and
the `queryset`.

Both queryset and manager work really well also when combibed. In the end is up to the developer
to decide which one it prefers better.

## Manager and QuerySet

When making queries within Mongoz, this return or an object if you want only one result or a
`queryset`/`manager` which is the internal representation of the results.

If you are familiar with Django querysets, this is **almost** the same and by almost is because
mongoz restricts loosely queryset variable assignments.

Let us get familar with queries.

Let us assume you have the following `User` document defined.

```python
{!> ../docs_src/queries/document.py !}
```

As mentioned before, Mongoz allows to use two ways of querying. Via `manager` and via `queryset`.
Both allow chain calls, for instance, `sort()` with a `limit()` combined.

For instance, let us create a user.

=== "Manager"

    ```python
    user = await User.objects.create(
        first_name="Mongoz", last_name="ODM", email="mongoz@mongoz.com",
        password="Compl3x!pa$$"
    )
    ```

=== "QuerySet"

    ```python
    user = await User(
        first_name="Mongoz", last_name="ODM", email="mongoz@mongoz.com",
        password="Compl3x!pa$$"
    ).create()
    ```

As you can see, the **manager** uses the `objects` to access the operations and the `queryset` does
it in a different way.

For those familiar with Django, the `manager` follows the same lines.

Let us now query the database to obtain a simple record but filtering it by `email` and `first_name`.
We want this to return a list since we are using a `filter`.

=== "Manager"

    ```python
    users = await User.objects.filter(
        email="mongoz@mongoz.com", first_name="Mongo"
    )
    ```

=== "QuerySet"

    ```python
    users = await User.query(User.email == "mongoz@mongoz.com").query(
        User.first_name == "Mongo"
    ).all()
    ```

Quite simple right? Well yes, although preferably we would recommend the use of the `manager` for
almost everything you can do with Mongoz, sometimes using the `queryset` can be also useful if
you like different syntaxes. This syntax was inspired by Mongox.

## Returning managers/querysets

There are many operations you can do with the managers/querysets and then you can also leverage those
for your use cases.

The following operators return `managers`/`querysets` which means you can combine different
operators at the same time.

This also means you can nest multiple different and same types. For example:

```python
await User.objects.filter(...).sort(...).filter(...).limit(2)
```

Every single operation that returns managers and querysets allows combined/nested calls.

### Filter

The `filter` is unique to the `manager` and it does not exist in this way in the `queryset`.
The `queryset` version is the [Query](#query).

#### Django-style

These filters are the same **Django-style** lookups.

```python
users = await User.objects.filter(is_active=True, email__icontains="gmail")
```

The same special operators are also automatically added on every column.

* **in** - The `IN` operator.
* **not_in** - The opposide of `in`, meaning, all the records that are not in the condition.
* **contains** - Filter instances that contains a specific value.
* **icontains** - Filter instances that contains a specific value but case-insensitive.
* **lt** - Filter instances having values `Less Than`.
* **lte** - Filter instances having values `Less Than Equal`.
* **gt** - Filter instances having values `Greater Than`.
* **gte** - Filter instances having values `Greater Than Equal`.
* **asc** - Filter instances by ascending order where `_asc=True`.
* **desc** - Filter instances by descending order where `_desc=True`.
* **neq** - Filter instances by not equal to condition.

##### Example

```python
users = await User.objects.filter(email__icontains="foo")
users = await User.objects.filter(id__in=[1, 2, 3])
users = await User.objects.filter(id__not_in=[1, 2, 3])
users = await User.objects.filter(id__gt=1)
users = await User.objects.filter(id__lte=3)
users = await User.objects.filter(id__lt=2)
users = await User.objects.filter(id__gte=4)
users = await User.objects.filter(id__asc=True)
users = await User.objects.filter(id__asc=False) # same as desc True
users = await User.objects.filter(id__desc=True)
users = await User.objects.filter(id__desc=False) # same as asc True
users = await User.objects.filter(id__neq=1) # same as asc True
```

### Using

Change the database while querying, only need to supply the database name in order to change the database.

=== "Manager"

    ```python
    users = await User.objects.using("my_mongo_db").all()
    ```

### Query

The `query` is what is used by the `queryset` instead of the `manager`. In other words, the `query`
is for the queryset what `filter` is for the `manager`.

An example query would be:

```python
users = await User.query(User.email == "mongoz@mongoz.com").query(User.id > 1).all()
```

Or alternatively you can use dictionaries.

```python
user = await User.query({"first_name": "Mongoz"}).all()
```

Or you can use the `User` fields instead of dictionaries.

```python
user = await User.query({User.first_name: "Mongoz"}).all()
```

### Limit

Limiting the number of results.

=== "Manager"

    ```python
    users = await User.objects.limit(1)

    users = await User.objects.filter(email__icontains="mongo").limit(2)
    ```

=== "QuerySet"

    ```python
    users = await User.query().limit(1)

    users = await User.query().sort(User.email, Order.ASCENDING).limit(2)
    ```

### Skip

Skip a certain number of documents.

=== "Manager"

    ```python
    users = await User.objects.filter(email__icontains="mongo").skip(1)
    ```

=== "QuerySet"

    ```python
    users = await User.query().skip(1)
    ```

### Raw

Executing raw queries directly. This allows to have some sort of power over some more complicated
queries you might find.

#### Simple and nested raw queries

=== "Manager"

    ```python
    # Simple raw query
    user = await Movie.objects.raw({"email": "mongoz@mongoz.com"}).get()
    users = await Movie.objects.raw({"email": "mongoz@mongoz.com"})

    # Nested raw queries
    user = await Movie.objects.raw({"name": "mongo"}).raw({"email": "mongoz@mongoz.com"}).get()
    users = await Movie.objects.raw({"name": "mongo"}).raw({"email": "mongoz@mongoz.com"})
    ```

=== "QuerySet"

    ```python
    # Simple raw query
    user = await Movie.query({"email": "mongoz@mongoz.com"}).get()
    users = await Movie.query({"email": "mongoz@mongoz.com"})

    # Nested raw queries
    user = await Movie.query({"name": "mongo"}).raw({"email": "mongoz@mongoz.com"}).get()
    users = await Movie.query({"name": "mongo"}).raw({"email": "mongoz@mongoz.com"})
    ```

#### Complex with MongoDB specific syntax

What if you want to level up and add extras?

=== "Manager"

    ```python
    users = await Movie.objects.raw(
        {"name": "Mongo"}).raw({"email": {"$regex": "mongo.com"}}
    )

    users = await Movie.objects.raw(
        {"$or": [{"name": "Another Mongo"}, {"email": {"$eq": "another@mongoz.com"}}]}
    )
    ```

=== "QuerySet"

    ```python
    users = await Movie.query(
        {"name": "Mongo"}).raw({"email": {"$regex": "mongo.com"}}
    )

    users = await Movie.query(
        {"$or": [{"name": "Another Mongo"}, {"email": {"$eq": "another@mongoz.com"}}]}
    )
    ```

### Sort

Sort the values based on keys. The sort like every single returning manager/queryset, allows
nested calls.

=== "Manager"

    ```python
    # Simple and nested sorts
    users = await User.objects.sort("name", Order.DESCENDING)
    users = await User.objects.sort("name", Order.DESCENDING).sort("email", Order.ASCENDING)

    # Using the filter
    users = await User.objects.sort(name__desc=True)
    users = await User.objects.sort(name__desc=True).sort(email__asc=True)

    # Using a list
    users = await User.objects.sort(
         [(User.name, Order.DESCENDING), (User.email, Order.DESCENDING)]
    )
    ```

=== "QuerySet"

    ```python
    # Simple and nested sorts
    users = await User.query().sort("name", Order.DESCENDING)
    users = await User.query().sort("name", Order.DESCENDING).sort("email", Order.ASCENDING)

    # Using a list
    users = await User.query().sort(
         [(User.name, Order.DESCENDING), (User.email, Order.DESCENDING)]
    )
    ```

The [Q](#the-q-operator) operator allows some combinations as well if you opt for that same syntax.

Now, can you combine the syntax of the sort from the `queryset` with the syntax of the `manager`
in the sort? **Yes you can**. An example would be something like this:

```python
users = await User.objects.sort(Q.desc(User.name)).sort(Q.asc(User.email)).all()
```

!!! Danger
    The syntax from the `queryset` is allowed inside the `manager` **but not the other way around**.

### None

If you only need to return an empty manager or queryset.

=== "Manager"

    ```python
    manager = await User.objects.none()
    ```

=== "QuerySet"

    ```python
    queryset = await User.query().none()
    ```

## Returning results

These are the operations that return results instead of *managers* or *querysets*. Which means
you cannot nest them.

### All

Returns all the instances.

=== "Manager"

    ```python
    users = await User.objects.all()
    users = await User.objects.filter(email="mongoz@mongoz.com").all()
    ```

=== "QuerySet"

    ```python
    users = await User.query().all()
    users = await User.query(User.email == "mongoz@mongoz.com").all()
    ```

### Save

This is a classic operation that is very useful depending on which operations you need to perform.
Used to save an existing object in the database. Slighly different from the [update](#update) and
simpler to read.

=== "Manager"

    ```python
    await User.objects.create(is_active=True, email="foo@bar.com")

    user = await User.objects.get(email="foo@bar.com")
    user.email = "bar@foo.com"

    await user.save()
    ```

=== "QuerySet"

    ```python
    await User(is_active=True, email="foo@bar.com").create()

    user = await User.query(User.email == "foo@bar.com").get()
    user.email = "bar@foo.com"

    await user.save()
    ```

Now a more unique, yet possible scenario with a save. Imagine you need to create an exact copy
of an object and store it in the database. These cases are more common than you think but this is
for example purposes only.

=== "Manager"

    ```python
    await User.objects.create(is_active=True, email="foo@bar.com", name="John Doe")

    user = await User.objects.get(email="foo@bar.com")
    # User(id=ObjectId(...))

    # Making a quick copy
    user.id = None
    new_user = await user.save()
    # User(id=ObjectId(...))
    ```

=== "QuerySet"

    ```python
    await User(is_active=True, email="foo@bar.com", name="John Doe").create()

    user = await User.query(User.email == "foo@bar.com").get()
    # User(id=ObjectId(...))

    # Making a quick copy
    user.id = None
    new_user = await user.save()
    # User(id=ObjectId(...))
    ```

### Delete

Used to delete an instance.

=== "Manager"

    ```python
    await User.objects.filter(email="foo@bar.com").delete()
    ```

=== "QuerySet"

    ```python
    await Movie.query({User.email: "foo@bar.com"}).delete()
    ```

Or directly in the instance.

=== "Manager"

    ```python
    user = await User.objects.get(email="foo@bar.com")

    await user.delete()
    ```

=== "QuerySet"

    ```python
    await Movie.query({User.email: "foo@bar.com"}).delete()

    await user.delete()
    ```

### Update

You can update document instances by calling this operator.

=== "Manager"

    ```python
    user = await User.objects.get(email="foo@bar.com")

    await user.update(email="bar@foo.com")
    ```

=== "QuerySet"

    ```python
    user = await User.query(User.email == "foo@bar.com").get()

    await user.update(email="bar@foo.com")
    ```

There is also the possibility of updating all the records based on a specific search.

=== "Manager"

    ```python
    user = await User.objects.filter(id__gt=1).update(name="MongoZ")
    user = await User.objects.filter(id__gt=1).update_many(name="MongoZ")
    ```

=== "QuerySet"

    ```python
    user = await User.query(User.id > 1).update(name="MongoZ")
    user = await User.query(User.id > 1).update_many(name="MongoZ")
    ```

### Get

Obtains a single record from the database.

=== "Manager"

    ```python
    user = await User.objects.get(email="foo@bar.com", name="Mongoz")
    ```

=== "QuerySet"

    ```python
    user = await User.query(User.email == "foo@bar.com").query(User.name == "Mongoz").get()
    ```

You can mix the queryset returns with this operator as well.

=== "Manager"

    ```python
    user = await User.objects.filter(email="foo@bar.com").get()
    ```

=== "QuerySet"

    ```python
    user = await User.query().query(User.email == "foo@bar.com").get()
    ```

### First

When you need to return the very first result from a queryset.

=== "Manager"

    ```python
    user = await User.objects.first()
    ```

=== "QuerySet"

    ```python
    user = await User.query().first()
    ```

You can also apply filters when needed.

=== "Manager"

    ```python
    user = await User.objects.filter(email="foo@bar.com").first()
    ```

=== "QuerySet"

    ```python
    user = await User.query(User.email == "foo@bar.com").first()
    ```

### Last

When you need to return the last result from a queryset.

=== "Manager"

    ```python
    user = await User.objects.last()
    ```

=== "QuerySet"

    ```python
    user = await User.query().last()
    ```

You can also apply filters when needed.

=== "Manager"

    ```python
    user = await User.objects.filter(name="mongoz").last()
    ```

=== "QuerySet"

    ```python
    user = await User.query(User.email == "mongoz").last()
    ```

### Count

Returns an integer with the total of records.

=== "Manager"

    ```python
    total = await User.objects.count()
    ```

=== "QuerySet"

    ```python
    total = await User.query().count()
    ```

### Exclude

The `exclude()` is used when you want to filter results by excluding instances.

=== "Manager"

    ```python
    users = await User.objects.exclude(is_active=False)
    ```

=== "QuerySet"

    ```python
    users = await User.query(Q.not_(User.is_active, False)).all()
    ```

    With the queryset we simply call the [Not](#not) operator.

### Values

Returns the model results in a dictionary like format.

=== "Manager"

    ```python
    await User.objects.create(name="John" email="foo@bar.com")

    # All values
    user = User.objects.values()
    users == [
        {"id": 1, "name": "John", "email": "foo@bar.com"},
    ]

    # Only the name
    user = User.objects.values("name")
    users == [
        {"name": "John"},
    ]
    # Or as a list
    # Only the name
    user = User.objects.values(["name"])
    users == [
        {"name": "John"},
    ]

    # Exclude some values
    user = User.objects.values(exclude=["id"])
    users == [
        {"name": "John", "email": "foo@bar.com"},
    ]
    ```

=== "QuerySet"

    ```python
    await User(name="John" email="foo@bar.com").create()

    # All values
    user = User.query().values()
    users == [
        {"id": 1, "name": "John", "email": "foo@bar.com"},
    ]

    # Only the name
    user = User.query().values("name")
    users == [
        {"name": "John"},
    ]
    # Or as a list
    # Only the name
    user = User.query().values(["name"])
    users == [
        {"name": "John"},
    ]

    # Exclude some values
    user = User.query().values(exclude=["id"])
    users == [
        {"name": "John", "email": "foo@bar.com"},
    ]
    ```

The `values()` can also be combined with `filter`, `only` as per usual.

**Parameters**:

* **fields** - Fields of values to return.
* **exclude** - Fields to exclude from the return.
* **exclude_none** - Boolean flag indicating if the fields with `None` should be excluded.

### Values list

Returns the model results in a tuple like format.

=== "Manager"

    ```python
    await User.objects.create(name="John" email="foo@bar.com")

    # All values
    user = User.objects.values_list()
    users == [
        (1, "John" "foo@bar.com"),
    ]

    # Only the name
    user = User.objects.values_list("name")
    users == [
        ("John",),
    ]
    # Or as a list
    # Only the name
    user = User.objects.values_list(["name"])
    users == [
        ("John",),
    ]

    # Exclude some values
    user = User.objects.values(exclude=["id"])
    users == [
        ("John", "foo@bar.com"),
    ]

    # Flattened
    user = User.objects.values_list("email", flat=True)
    users == [
        "foo@bar.com",
    ]
    ```

=== "QuerySet"

    ```python
    await User(name="John" email="foo@bar.com").create()

    # All values
    user = User.query().values_list()
    users == [
        (1, "John" "foo@bar.com"),
    ]

    # Only the name
    user = User.query().values_list("name")
    users == [
        ("John",),
    ]
    # Or as a list
    # Only the name
    user = User.query().values_list(["name"])
    users == [
        ("John",),
    ]

    # Exclude some values
    user = User.query().values(exclude=["id"])
    users == [
        ("John", "foo@bar.com"),
    ]

    # Flattened
    user = User.query().values_list("email", flat=True)
    users == [
        "foo@bar.com",
    ]
    ```

The `values_list()` can also be combined with `filter`, `only` as per usual.

**Parameters**:

* **fields** - Fields of values to return.
* **exclude** - Fields to exclude from the return.
* **exclude_none** - Boolean flag indicating if the fields with `None` should be excluded.
* **flat** - Boolean flag indicating the results should be flattened.


### Only

Returns the results containing **only** the fields in the query and nothing else.

=== "Manager"

    ```python
    await User.objects.create(name="John" email="foo@bar.com")

    user = await User.objects.only("name")
    ```

=== "QuerySet"

    ```python
    await User(name="John" email="foo@bar.com").create

    user = await User.query().only("name").all()
    ```

!!! Warning
    You can only use `only()` or `defer()` but not both combined or a `FieldDefinitionError` is raised.

### Defer

Returns the results containing all the fields **but the ones you want to exclude**.

=== "Manager"

    ```python
    await User.objects.create(name="John" email="foo@bar.com")

    user = await User.objects.defer("name")
    ```

=== "QuerySet"

    ```python
    await User(name="John" email="foo@bar.com").create

    user = await User.query().defer("name").all()
    ```

!!! Warning
    You can only use `only()` or `defer()` but not both combined or a `FieldDefinitionError` is raised.


### Get or none

When querying a document and do not want to raise a [DocumentNotFound](./exceptions.md#documentnotfound) and
instead returns a `None`.

=== "Manager"

    ```python
    user = await User.objects.get_or_none(id=1)
    ```

=== "QuerySet"

    ```python
    user = await User.query(User.id == 1).get_or_none()
    ```

### Where

Apply raw string queries or the `where` clause.

=== "Manager"

    ```python
    user = await User.objects.where("this.email == 'foo@bar.com'")
    ```

=== "QuerySet"

    ```python
    user = await User.query().where("this.email == 'foo@bar.com'")
    ```

### Distinct values

Filter by distinct values and return a list of those same values.

=== "Manager"

    ```python
    user = await User.objects.distinct_values("email")
    ```

=== "QuerySet"

    ```python
    user = await User.query().distinct_values("email")
    ```

### Get document by id

Get a document by the `_id`. This functionality accepts the parameter `id` as string or `bson.ObjectId`.

=== "Manager"

    ```python
    user = await User.objects.create(
        first_name="Foo", last_name="Bar", email="foo@bar.com"
    )

    user = await User.objects.get_document_by_id(user.id)
    ```

=== "Queryset"

    ```python
    user = await User(
        first_name="Foo", last_name="Bar", email="foo@bar.com"
    ).create()

    user = await User.query().get_document_by_id(user.id)
    ```

## Useful methods

### Get or create

When you need get an existing document instance from the matching query. If exists, returns or creates
a new one in case of not existing.

=== "Manager"

    ```python
    user = await User.objects.get_or_create(email="foo@bar.com", defaults={
        "is_active": False, "first_name": "Foo"
    })
    ```

=== "QuerySet"

    ```python
    user = await User.query().get_or_create(
        {User.is_active: False, User.first_name: "Foo", User.email: "foo@bar.com"}
    )
    ```

This will query the `User` document with the `email` as the lookup key. If it doesn't exist, then it
will use that value with the `defaults` provided to create a new instance.

### Bulk create

When you need to create many instances in one go, or `in bulk`.

=== "Manager"

    ```python
    user_names = ("MongoZ", "MongoDB")
    models = [
        User(first_name=name, last_name=name, email=f"{name}@mongoz.com") for name in user_names
    ]

    users = await User.objects.bulk_create(models)
    ```

=== "QuerySet"

    ```python
    user_names = ("MongoZ", "MongoDB")
    models = [
        User(first_name=name, last_name=name, email=f"{name}@mongoz.com") for name in user_names
    ]

    users = await User.query().bulk_create(models)
    ```

### Bulk update

When you need to update many instances in one go, or `in bulk`.

=== "Manager"

    ```python
    data = [
        {"email": "foo@bar.com", "first_name": "Foo", "last_name": "Bar", "is_active": True},
        {"email": "bar@foo.com", "first_name": "Bar", "last_name": "Foo", "is_active": True}
    ]
    users = [User(**user_data.model_dump()) for user_data in data]
    await User.objects.bulk_create(users)

    users = await User.objects.all()

    await User.objects.filter().bulk_update(is_active=False)
    ```

=== "QuerySet"

    ```python
    data = [
        {"email": "foo@bar.com", "first_name": "Foo", "last_name": "Bar", "is_active": True},
        {"email": "bar@foo.com", "first_name": "Bar", "last_name": "Foo", "is_active": True}
    ]
    users = [User(**user_data.model_dump()) for user_data in data]
    await User.objects.bulk_create(users)

    users = await User.objects.all()

    await User.query().bulk_update(is_active=False)
    ```

## Note

When applying the functions that returns values directly and not managers or querysets,
**you can still apply the operators such as `filter`, `skip`, `sort`...**

## Querying Embedded documents

Querying [embedded documents](./embedded-documents.md) is also easy and here the `queryset` is very powerful in doing it so.

Let us see an example.

```python hl_lines="17"
{!> ../docs_src/queries/embed.py !}
```

We can now create some instances of the `User`.

=== "Manager"

    ```python hl_lines="5"
    access_type = UserType(access_level="admin")

    await User.objects.create(
        first_name="Mongoz", last_name="ODM", email="mongoz@mongoz.com",
        access_level=access_type
    )
    ```

=== "QuerySet"

    ```python hl_lines="5"
    access_type = UserType(access_level="admin")

    await User(
        first_name="Mongoz", last_name="ODM", email="mongoz@mongoz.com",
        access_level=access_type
    ).create()
    ```

This will create the following document in the database:

```json
{
    "email": "mongoz@mongoz.com", "first_name": "Mongoz", "last_name": "ODM",
    "is_active": true, "access_level": {"level": "admin" }
},
```

You can now query the user by embedded document field.

```python
await User.query(User.user_type.level == "admin").get()
```

This is the equivalent to the following filter:

```json
{"access_level.level": "admin" }
```

You can also use the complete embedded document.

```python
await User.query(User.user_type == level).get()
```

This is the equivalent to the following filter:

```json
{"access_level": {"level": "admin"} }
```

!!! Warning
    For the [Embedded Documents](./embedded-documents.md) type of query, using the manager it won't
    work. **You should use the `queryset` type of approach for the query**.

## The Q operator

This operator was inspired by `Mongox` and extended for Mongoz needs. The credit for the initial
design of the `Q` operator goes to `Mongox`.

The `Q` class contains some useful and quite handy methods to be used in the queries.

```python
from mongoz import Q, Order
```

The `Q` operator is mainly used in the `queryset` and not so much in the `manager` and the main
reason for this is because the `manager` internally manipulates the `Q` operator for you
automatically. Pretty cool, hein?

In order to create, for example a `sort` query, you would usually do this:

```python
users = await User.query().sort(User.email, Order.DESCENDING).all()
```

Where does the `Q` operator enters here? Well, you can see it as a shortcut for your queries.

### Ascending

```python
users = await User.query().sort(Q.asc(User.email)).all()
```

### Descending

```python
users = await User.query().sort(Q.desc(User.email)).all()
```

### In

The `in` operator.

```python
users = await User.query(Q.in_(User.id, [1, 2, 3, 4])).all()
```

### Not In

The `not_in` operator.

```python
users = await User.query(Q.not_in(User.id, [1, 2, 3, 4])).all()
```

### And

```python
users = await User.query(Q.and_(User.email == "foo@bar.com", User.id > 1)).all()

users = await User.query(User.email == "foo@bar.com").query(User.id > 1).all()
```

### Or

```python
users = await User.query(Q.or_(User.email == "foo@bar.com", User.id > 1)).all()
```

### Nor

```python
users = await User.query(Q.nor_(User.email == "foo@bar.com", User.id > 1)).all()
```

### Not

```python
users = await User.query(Q.not_(User.email, "foo@bar.com")).all()
```

### Contains

```python
users = await User.query(Q.contains(User.email, "foo")).all()
```

### IContains

```python
users = await User.query(Q.icontains(User.email, "foo")).all()
```

### Pattern

Applies some `$regex` patterns.

```python
users = await User.query(Q.pattern(User.email, r"\w+ foo \w+")).all()
```

### Equals

The `equals` operator.

```python
users = await User.query(Q.eq(User.email, "foo@bar.com")).all()
```

### Not Equals

The `not equals` operator.

```python
users = await User.query(Q.neq(User.email, "foo@bar.com")).all()
```

### Where

Applying the mongo `where` operator.

```python
users = await User.query(Q.where(User.email, "foo@bar.com")).all()
```

### Greater Than

```python
users = await User.query(Q.gt(User.id, 1)).all()
```

### Greater Than Equal

```python
users = await User.query(Q.gte(User.id, 1)).all()
```

### Less Than

```python
users = await User.query(Q.lt(User.id, 20)).all()
```

### Less Than Equal

```python
users = await User.query(Q.lte(User.id, 20)).all()
```

## Blocking Queries

What happens if you want to use Mongoz with a blocking operation? So by blocking means `sync`.
For instance, Flask does not support natively `async` and Mongoz is an async agnotic ORM and you
probably would like to take advantage of Mongoz but you want without doing a lot of magic behind.

Well, Mongoz also supports the `run_sync` functionality that allows you to run the queries in
*blocking* mode with ease!

### How to use

You simply need to use the `run_sync` functionality from Mongoz and make it happen almost immediatly.

```python
from mongoz import run_sync
```

All the available functionalities of Mongoz run within this wrapper without extra syntax.

Let us see some examples.

**Async mode**

```python
await User.objects.all()
await User.objects.filter(name__icontains="example")
await User.objects.create(name="Mongoz")
```

**With run_sync**

```python
from mongoz import run_sync

run_sync(User.objects.filter(name__icontains="example"))
run_sync(User.objects.create(name="Mongoz"))
```

[document]: ./documents.md
