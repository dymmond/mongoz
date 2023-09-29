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



[document]: ./documents.md
