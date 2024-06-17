# Excepções

Todas as exceções personalizadas do **Mongoz** derivam da base `MongozException`.

## DocumentNotFound

Lançada quando uma instância de documento é pesquisado e não existe.

```python
from mongoz.exceptions import DocumentNotFound
```

Ou simplesmente:

```python
from mongoz import DocumentNotFound
```

## MultipleDocumentsReturned

Lançada quando uma consulta a um documento retorna vários resultados para o resultado da pequisa fornecida.

```python
from mongoz.exceptions import MultipleDocumentsReturned
```

Ou simplesmente:

```python
from mongoz import MultipleDocumentsReturned
```

## AbstractDocumentError

Lançada quando um documento abstrato `abstract=True` está a tentar ser guardado.

```python
from mongoz.exceptions import AbstractDocumentError
```

## ImproperlyConfigured

Lançada quando há uma má configuração nos documentos e metaclasses.

```python
from mongoz.exceptions import ImproperlyConfigured
```

Ou simplesmente:

```python
from mongoz import ImproperlyConfigured
```

## IndexError

Lançada quando há uma má configuração nos índices.

```python
from mongoz.exceptions import IndexError
```

## FieldDefinitionError

Lançada quando há uma má configuração na definição dos campos.

```python
from mongoz.exceptions import FieldDefinitionError
```

## SignalError

Lançada quando há uma má configuração nos sinais do documento.

```python
from mongoz.exceptions import SignalError
```
