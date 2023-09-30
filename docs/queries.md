# Queries

Making queries is a must when using an ODM and being able to make complex queries is even better
when allowed.

MongDB is known for its performance when querying a database and it is very fast. T

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

## QuerySet and Manager

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
await User.manager.filter(...).sort(...).filter(...).limit(2)
```

Every single operation that returns managers and querysets allows combined/nested calls.

### Filter

The `filter` is unique to the `manager` and it does not exist in this way in the `queryset`.
The `queryset` version is the [Query](#query).

#### Django-style

These filters are the same **Django-style** lookups.

```python
users = await User.query.filter(is_active=True, email__icontains="gmail")
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
users = await User.query.filter(email__icontains="foo")
users = await User.query.filter(id__in=[1, 2, 3])
users = await User.query.filter(id__not_in=[1, 2, 3])
users = await User.query.filter(id__gt=1)
users = await User.query.filter(id__lte=3)
users = await User.query.filter(id__lt=2)
users = await User.query.filter(id__gte=4)
users = await User.query.filter(id__asc=True)
users = await User.query.filter(id__asc=False) # same as desc True
users = await User.query.filter(id__desc=True)
users = await User.query.filter(id__desc=False) # same as asc True
users = await User.query.filter(id__neq=1) # same as asc True
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
    users = await User.query.limit(1)

    users = await User.query.filter(email__icontains="mongo").limit(2)
    ```

=== "QuerySet"

    ```python
    users = await User.query().limit(1)

    users = await User.query.sort(User.email, Order.ASCENDING).limit(2)
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

## The Q operator

[document]: ./documents.md
