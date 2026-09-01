# Exceptions

Mongoz-owned errors derive from `MongozException`. Every public exception is available from both
the top-level package and `mongoz.exceptions`:

```python
from mongoz import DocumentNotFound, MongozException, SignalError
from mongoz.exceptions import FieldDefinitionError, InvalidKeyError
```

Exception messages preserve every supplied context fragment with readable separators. The optional
`detail=` keyword remains supported. `DocumentNotFound` and `MultipleDocumentsReturned` provide
useful default messages even when the query path does not add more context.

## DocumentNotFound

`DocumentNotFound` is raised when a single-document query or acknowledged instance write finds no
matching persisted document. Catch it when absence is an expected application outcome.

## Exception taxonomy

| Exception | Meaning |
| :--- | :--- |
| `MongozException` | Base class for semantics owned by Mongoz. |
| `DocumentNotFound` | A query or acknowledged instance write found no matching document. |
| `MultipleDocumentsReturned` | A single-result query matched more than one document. |
| `ImproperlyConfigured` | Document metadata, settings, or another public configuration is invalid. |
| `FieldDefinitionError` | A field definition or field-oriented query argument is invalid. |
| `InvalidKeyError` | A requested field, identifier, index, or update key is invalid. |
| `InvalidObjectIdError` | An object identifier fails Mongoz-owned validation. |
| `SignalError` | Signal registration or broadcaster configuration is invalid. |
| `AbstractDocumentError` | A database operation was attempted on an abstract document. |
| `OperatorInvalid` | A lookup or query operator is unknown or receives an invalid operand. |
| `IndexError` | Index metadata or reconciliation policy is invalid. This is `mongoz.IndexError`, not Python's built-in `IndexError`. |

Catch the narrow semantic error where recovery is possible, or `MongozException` when one boundary
handles every Mongoz-owned contract error:

```python
from mongoz import DocumentNotFound, MongozException

try:
    user = await User.query(User.email == email).get()
except DocumentNotFound:
    user = None
except MongozException:
    raise
```

## Native PyMongo errors

Mongoz does not translate errors that remain owned by PyMongo or MongoDB. `DuplicateKeyError`,
`BulkWriteError`, server-selection failures, write-concern failures, and session or transaction
errors propagate unchanged. Catch those native classes from `pymongo.errors` when the application
has a database-specific recovery policy.
