# Campos

Os campos são utilizados na declaração do [documento](./documents.md) (tipos de dados) e definem quais tipos serão criados no base de dados.

A declaração de documentos no Mongoz com tipagem é apenas visual. As validações dos campos não são feitas pela tipagem do atributo dos documentos, mas sim pelos campos do Mongoz.

Tenha a certeza de que todas as validações são feitas por meio da validação do Pydantic, como de costume, nada muda.

## Tipos de dados

Como o **Mongoz** é uma nova abordagem em cima do Pydantic, os seguintes argumentos de palavra-chave são suportados em **todos os tipos de campos**.

* **default** - Um valor ou uma função.
* **index** - Um booleano. Determina se um índice de base de dados deve ser criado.
* **unique** - Um booleano. Determina uma restrição única.

Todos os campos são obrigatórios, a menos que um dos seguintes seja definido:

* **null** - Um booleano. Determina se uma coluna permite nulo.

    <sup>Defina o padrão como `None`</sup>

Todos os valores que pode passar em qualquer [Campo](https://docs.pydantic.dev/latest/concepts/fields/) do Pydantic também são 100% permitidos nos campos do Mongoz.

### Importando campos

Existem algumas maneiras de fazer isso e são as seguintes:

```python
import mongoz
```

A partir do `mongoz`, pode aceder a todos os campos disponíveis.

```python
from mongoz.core.db import fields
```

A partir de `fields`, deve ser capaz de aceder aos campos diretamente.

```python
from mongoz.core.db.fields import Integer
```

Pode importar diretamente o campo desejado.

Todos os campos têm parâmetros específicos além dos mencionados em [tipos de dados](#tipos-de-dados).

#### ObjectId

Este é um campo especial que estende diretamente o `bson.ObjectId` e adiciona alguma tipagem do Pydantic
para garantir que possa ser serializado corretamente.

```python
import mongoz


class MyDocument(mongoz.Document):
    an_id: ObjectId = mongoz.ObjectId()
```

#### NullableObjectId

Este é outro campo especial que estende o `bson.ObjectId` e, ao contrário do [ObjectId](#objectid),
este permite especificar campos nulos e não nulos visto que deriva do FieldFactory do Mongoz.

Por defeito, é definido como `null=True` e pode ser especificado como `null=False`, se necessário.

**Por defeito**

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

##### Parâmetros:

* **max_length** - Um inteiro a indicar o comprimento total da string.
* **min_length** - Um inteiro a indicar o comprimento mínimo da string.

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

Deriva do mesmo que [Integer](#integer) e valida o número decimal de ponto flutuante.

##### Parâmetros:

* **minimum** - Um inteiro, float ou decimal a indicar o mínimo.
* **maximum** - Um inteiro, float ou decimal a indicar o máximo.
* **max_digits** - Máximo de dígitos permitidos.
* **multiple_of** - Um inteiro, float ou decimal a indicar o múltiplo de.
* **decimal_places** - O total de casas decimais.

#### Decimal

```python
import decimal
import mongoz

class MyDocument(mongoz.Document):
    price: decimal.Decimal = mongoz.Decimal(max_digits=5, decimal_places=2, null=True)
```

Esta operação retornará o tipo `bson.Decimal128`, que pode ser convertido para string, float ou qualquer tipo normal, incluindo `to_decimal()` para converter para um campo nativo `decimal.Decimal`.

##### Parâmetros

* **minimum** - Um inteiro a indicar o mínimo.
* **maximum** - Um inteiro a indicar o máximo.
* **max_digits** - Um inteiro a indicar o total máximo de dígitos.
* **decimal_places** - Um inteiro a indicar o total de casas decimais.
* **multiple_of** - Um inteiro, float ou decimal a indicar o múltiplo de.

#### Boolean

```python
import mongoz


class MyDocument(mongoz.Document):
    is_active: bool = mongoz.Boolean(default=True)
    is_complete: bool = mongoz.Boolean(default=False)
```

#### DateTime

```python
import datetime
import mongoz


class MyDocument(mongoz.Document):
    created_at: datetime.datetime = mongoz.DateTime(default=datetime.datetime.now)
```

##### Parâmetros

* **auto_now** - Um booleano a indicar se o `auto_now` está "on".
* **auto_now_add** - Um booleano a indicar se o `auto_now_add` está "on".


#### Date

```python
import datetime
import mongoz


class MyDocument(mongoz.Document):
    created_at: datetime.date = mongoz.Date(default=datetime.date.today)
    ...
```

##### Parâmetros

* **auto_now** - Um booleano a indicar se o `auto_now` está "on".
* **auto_now_add** - Um booleano a indicar se o `auto_now_add` está "on".

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

Uma representação do objeto a ser guardado, por exemplo, um `JSON`.

#### UUID

```python
from uuid import UUID
import mongoz


class MyDocument(mongoz.Document):
    uuid: UUID = fields.UUID()
```

Deriva do mesmo que [String](#string) e valida o valor de um UUID.

#### Array

Este é um campo especial do Mongoz que declara e define um `Array` (lista) de um determinado tipo.
Por exemplo, se deseja guardar uma lista de strings ou qualquer outro tipo, **mas não misturado**.

```python
import mongoz


class MyDocument(mongoz.Document):
    tags: List[str] = fields.Array(str)
```

Isto pode ser particularmente útil se deseja especificar exactamente qual tipo deseja guardar e
nada mais.

##### Parâmetros

* **type_of** - O tipo específico a ser guardado, por exemplo, `str`.

#### ArrayList

Este é outro campo especial do Mongoz que declara e define um `ArrayList` (lista) de qualquer tipo.
Por exemplo, se deseja guardar uma lista de strings, inteiros ou qualquer outro tipo e **pode ser misturado**.

```python
import mongoz


class MyDocument(mongoz.Document):
    tags: List[Union[str, int, float]] = fields.ArrayList()
```

Isto pode ser particularmente útil se deseja especificar exactamente qual tipo deseja guardar e
nada mais.

#### Embed

Este é o campo onde os [Documentos Incorporados](./embedded-documents.md) são declarados.

```python
import mongoz

class Award(mongoz.EmbeddedDocument):
    name: str = mongoz.String()


class MyDocument(mongoz.Document):
    award: Award = fields.Embed(Award)
```

##### Parâmetros

* **document** - O tipo específico de documento incorporado. Se o `document` não for do tipo
`mongoz.EmbeddedDocument`, será lançado um `FieldDefinitionError`.
