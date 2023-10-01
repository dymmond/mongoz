# Exceptions

All **Mongoz** custom exceptions derive from the base `MongozException`.

## DocumentNotFound

Raised when querying a document instance and it does not exist.

```python
from mongoz.exceptions import DocumentNotFound
```

Or simply:

```python
from mongoz import DocumentNotFound
```

## MultipleDocumentsReturned

Raised when querying a document and returns multiple results for the given query result.

```python
from mongoz.exceptions import MultipleDocumentsReturned
```

Or simply:

```python
from mongoz import MultipleDocumentsReturned
```

## AbstractDocumentError

Raised when an abstract document `abstract=True` is trying to be saved.

```python
from mongoz.exceptions import AbstractDocumentError
```

## ImproperlyConfigured

Raised when misconfiguration in the models and metaclass is passed.

```python
from mongoz.exceptions import ImproperlyConfigured
```

Or simply:

```python
from mongoz import ImproperlyConfigured
```

## IndexError

Raised when there is a misconfiguration with the indexes.

```python
from mongoz.exceptions import IndexError
```

## FieldDefinitionError

Raised when there is a misconfiguration with the definition of the fields.

```python
from mongoz.exceptions import FieldDefinitionError
```

## SignalError

Raised when there is a misconfiguration with the document signals.

```python
from mongoz.exceptions import SignalError
```
