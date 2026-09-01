---
title: Operators and raw queries
description: Use Mongoz comparison, membership, string, and logical operators while keeping raw MongoDB and regex boundaries trusted.
---

# Operators and raw queries

Manager keyword lookups use `field__operator=value`. Field expressions and `Q` provide an explicit
alternative.

```python
adults = User.objects.filter(age__gte=18)
staff = User.query(Q.in_(User.role, ["admin", "editor"]))
```

## Literal string helpers

`contains`, `icontains`, `startswith`, `endswith`, `istartswith`, and `iendswith` escape regular
expression metacharacters. Their input is literal text, not a raw regex.

```python
literal = User.objects.filter(name__contains="a.b")
```

The query matches the characters `a.b`, not any-character regex semantics.

`Q.pattern(field, pattern)` is the explicit raw regex interface:

```python
trusted_pattern = User.query(Q.pattern(User.name, r"^A(?:da|lan)$"))
```

!!! warning "Regex input"
    Raw patterns are developer-authored trusted structures. Bound user search length and complexity
    even when using literal helpers. Do not expose arbitrary regex compilation as a public request
    feature without a separate threat model and execution budget.

## Raw dictionaries

`Manager.raw()`, dictionary arguments to `Document.query()`, raw `Expression` objects, aggregation
pipelines, bulk-write requests, and `collection.driver` pass native MongoDB structures through.

```python
trusted = User.objects.raw({"profile.flags": {"$all": ["verified"]}})
```

Never forward a decoded request mapping into one of these interfaces. Build an allowlisted query in
application code and apply authorization and tenant predicates independently.

## `$where`

`where()` is a legacy escape hatch for server-side JavaScript. MongoDB 8.0 deprecates server-side
JavaScript, `$where` cannot use indexes, and interpolated input is dangerous. Prefer ordinary
operators or `$expr`. Existing `$where` use should be treated as migration debt, not a recommended
query technique.
