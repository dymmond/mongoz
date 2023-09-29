# Embedded documents

Embedded documents are document to be embedded in `mongoz.Document`. The difference between one and
the other is that the `EmbeddedDocument` are not inserted separately and do not have a separate
`_id`.

To define an `EmbeddedDocument` you should inherit from `mongoz.EmbeddedDocument` and define the
[fields](./fields.md) in the way you would define for any other `mongoz.Document`.

```python hl_lines="4 10 14-15 19 23 28 30-31"
{!> ../docs_src/documents/embed.py !}
```

As you can see, the `EmbeddedDocument` is not a standlone document itself but part of the
[document](./documents.md) when declaring.

An `EmbeddedDocument` canm be used inside another and therefore creating a nested declaration
when saving the results.
