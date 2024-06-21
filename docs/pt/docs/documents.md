# Documentos

Como provavelmente já sabe, o MongoDB é uma base de dados NoSQL, o que significa que não possui tabelas, mas sim **documentos**.

Isso também significa que, com documentos e NoSQL, **não existem joins e chaves estrangeiras**.

O **Mongoz** implementa esses documentos numa interface mais amigável, caso ainda esteja familiarizado com ORMs ou mesmo se estiver a utilizar algo como o [Edgy][edgy]. Não há motivo para complicar muito, certo?

## Declaração de documentos

Ao declarar documentos, basta herdar do objeto `mongoz.Document` e definir os atributos usando os [Campos](./fields.md) do Mongoz.

Para cada documento definido, também precisa definir **um** campo obrigatório, o `registry`, que também é uma instância de `Registry` do Mongoz.

Existem mais parâmetros que pode usar e passar para o documento, como [tablename](#metaclass) entre outros, mas falaremos mais sobre isto nesta secção.

Como o **Mongoz** inspirou-se na interface do [Edgy][edgy], isto também significa que uma classe [Meta](#a-classe-meta) deve ser declarada.

Embora isto pareça muito simples, na verdade o **Mongoz** está a fazer muito trabalho por detrás.

```python
{!> ../../../docs_src/documents/declaring_models.py !}
```

### Documentos incorporados

Existe uma secção especial [aqui](./embedded-documents.md) dedicada a explicar o que são e como é simples usá-los com os documentos atuais.

## A classe Meta

Ao declarar um documento, é **crucial** ter a classe `Meta` declarada. É nela que declara os `metadados` necessários para seus documentos.

Atualmente, os parâmetros disponíveis para o meta são:

* **registry** - A instância do [registry](./registry.md) onde o documento será criado. Este campo é **obrigatório** e lançará um erro `ImproperlyConfigured` se nenhum registro for encontrado.

* **collection** - O nome da tabela (*collection*) na base de dados, **não o nome da classe**.

    <sup>Padrão: `nome da classe no plural`<sup>

* **database** - O nome da base de dados onde o documento será criado.
* **abstract** - Se o documento é abstracto ou não. Se for abstracto, ele não gerará a tabela do base de dados.

    <sup>Padrão: `False`<sup>

* **indexes** - Os índices personalizados extras que deseja adicionar ao documento.
* **autogenerate_index** - Se os índices devem ser gerados automaticamente pelo Mongoz.

    <sup>Padrão: `False`<sup>

### Registry

Trabalhar com um [registry](./registry.md) é o que torna o **Mongoz** dinâmico e muito flexível com a interface familiar que todos nós gostamos. Sem o registro, o documento não sabe de onde deve obter os dados.

Imagine um `registry` como uma ponte, porque é exatamente isso que ele faz.

Vamos ver alguns exemplos de como usar o registro com um design simples e com abordagens um pouco mais complexas.

#### Em poucas palavras

```python
{!> ../../../docs_src/documents/registry/nutshell.py !}
```

Como pode ver, ao declarar o `registry` e atribuí-lo ao `registry`, esse mesmo `registry` é usado no `Meta` do documento.

#### Com herança

Sim, também pode usar a herança de documentos para ajudá-lo com seus documentos e evitar repetições.

```python
{!> ../../../docs_src/documents/registry/inheritance_no_repeat.py !}
```

Como pode ver, as tabelas `User` e `Product` estão a herdar de `BaseDocument`, onde o `registry` já foi declarado. Desta forma, pode evitar repetições.

A razão para `abstract=True` é porque não queremos criar um documento dessa classe específica na base de dados.

Isto pode ser especialmente útil se tiver mais de um `registry` no sistema e quiser dividir as bases por responsabilidades.

#### Com classes abstratas

E se classe for abstrata? Ainda é possível herdar o registro?

Claro! Isso não muda com o registro.

```python
{!> ../../../docs_src/documents/registry/inheritance_abstract.py !}
```

### Nome da tabela

Isto é realmente muito simples e também vem com padrões. Ao criar um [documento](#declaring-documents), se um campo `collection` no objeto `Meta` não for declarado, ele pluralizará a classe Python.

#### Documento sem nome de tabela

```python
{!> ../../../docs_src/documents/tablename/model_no_tablename.py !}
```

Como mencionado no exemplo, como uma `collection` não foi declarada, o **Mongoz** pluralizará o nome da classe Python `User` e ela tornar-se-á `users` na base de dados.

#### Documento com nome de tabela

```python
{!> ../../../docs_src/documents/tablename/model_with_tablename.py !}
```

Aqui, o `collection` está a ser declarado explicitamente como `users`. Embora corresponda à pluralização do nome da classe Python, isto também poderia ser algo diferente.

```python
{!> ../../../docs_src/documents/tablename/model_diff_tn.py !}
```

Neste exemplo, a classe `User` será representada por um mapeamento `db_users` na base de dados.

!!! Ti+
    Chamar `collection` com um nome diferente do da classe não altera o comportamento no código. Ainda acessará a tabela fornecida no código por meio da classe principal.

### Abstracto

Como o nome sugere, é quando deseja declarar um documento abstracto.

Porque é que precisa de um documento abstracto em primeiro lugar? Bem, pelo mesmo motivo quando precisa declarar uma classe abstrata em Python, mas para esse caso simplesmente não deseja criar uma tabela a partir dessa declaração de documento.

Isto pode ser útil se deseja ter funcionalidades comuns em vários documentos e não deseja repetir o código.

A maneira de declarar um documento abstracto no **Mongoz** é passar `True` para o atributo `abstract` na classe [meta](#the-meta-class).

#### Em poucas palavras

Neste documento, já mencionamos documentos abstratos e como usá-los, mas vamos usar mais exemplos para deixar tudo ainda mais claro.

```python
{!> ../../../docs_src/documents/abstract/simple.py !}
```

Este documento em si não faz muito sozinho. Ele simplesmente cria um `BaseDocument` e declara o [registry](#registry), bem como declara o `abstract` como `True`.

#### Use documentos abstratos para ter funcionalidades comuns

Aproveitar os documentos abstratos para ter funcionalidades comuns é geralmente o caso de uso comum em primeiro lugar.

Vamos ver um exemplo mais complexo e como usá-lo.

```python
{!> ../../../docs_src/documents/abstract/common.py !}
```

Este já é um exemplo bastante complexo, onde `User` e `Product` têm funcionalidades comuns, como o `id` e a `description`, bem como a função `get_description()`.

### Índices

Às vezes, pode querer adicionar índices criados especificamente para os seus documentos. Índices de base de dados também têm custos e **deve-se ter sempre cuidado** ao criar um.

O Mongoz fornece um objeto `Index` que deve ser usado ao declarar índices de documentos.

```python
from mongoz import Index, IndexType, Order
```

O `IndexType` possui os tipos de índice PyMongo suportados:

* `GEO2D`
* `GEOSPHERE`
* `HASHED`
* `TEXT`

O `Order` é a ordem PyMongo:

* `ASCENDING`
* `DESCENDING`

#### Parâmetros

Os parâmetros do `Index` são:

* **key** - O nome do campo (chave) para o índice.
* **keys** (Opcional) - Lista de tuplos Python (string, ordem) para o índice.
* **name** - O nome do índice.

O `Index` no Mongoz é uma extensão do [`pymongo.IndexModel`](https://pymongo.readthedocs.io/en/stable/api/pymongo/operations.html#pymongo.operations.IndexModel.document).

#### Criação dos índices

Ao criar um índice com o `mongoz`, pode-se fazer isso de três maneiras diferentes.

1. Declarar diretamente no campo, passando `index=True`.
2. Declarar no [Meta](#the-meta-class).
3. Combinar tanto o campo quanto a metaclass.

Quando eles são declarados, o `Mongoz` criará automaticamente esses índices se o `autogenerate_index` da [meta](#the-meta-class) for `True`.

Se o `autogenerated_index` for `False`, precisará [criar manualmente](#index-operations) os índices.

#### Índice simples

A maneira mais simples e limpa de declarar um índice com o **Mongoz**. Declara diretamente no campo do documento.

```python hl_lines="11"
{!> ../../../docs_src/documents/indexes/simple.py !}
```

#### Índice via Meta

```python hl_lines="17"
{!> ../../../docs_src/documents/indexes/simple2.py !}
```

#### Índices complexos

```python hl_lines="9 17-20"
{!> ../../../docs_src/documents/indexes/complex_together.py !}
```

### Operações de índice

Trabalhar com índices é bastante fácil e existem algumas operações que pode executar manualmente nos seus documentos e outras que **precisa executar manualmente**.

#### Criando índices

Quando os índices são declarados nos documentos, o Mongoz saberá o que fazer se você tiver definido a sinalização `autogenerate_index=True` na [metaclass](#the-meta-class).

A função `create_indexes()` é usada para criar todos os índices declarados.

Se a sinalização estiver definida como `False`, pode simplesmente criar os índices chamando:

```python
await MyDocument.create_indexes()
```

Por exemplo, usando o documento `User` anterior, seria algo como:

```python
await User.create_indexes()
```

#### Criar índices individuais

E se quiser criar manualmente apenas um índice? Bem, isso também é possível chamando `create_index()`.

!!! Tip
    Isto só é necessário se o `autogenerate_index` estiver definido como `False`, caso contrário, isto pode ser ignorado.

A sintaxe é muito clara e simples:

```python
await MyDocument.create_index(<NOME-DO-ÍNDICE>)
```

Por exemplo, usando o documento `User` anterior, onde o `name` também foi criado como um índice, seria algo como:

```python
await User.create_index("name")
```

!!! Warning
    Se tentar criar um índice com um nome do campo não declarado no documento ou não declarado como `index=True`, pelo menos, um `InvalidKeyError` será lançado.

#### Excluindo índices

Agora, vamos para o oposto da [criação de índices](#criando-índices) e isso **deve ser feito manualmente**.

A função `drop_indexes()` é usada para excluir todos os índices declarados no documento.

Observe que isto só excluirá os índices declarados no documento, portanto, pode ter certeza de que nenhum outro índice será afectado.

Por exemplo, usando o documento `User` anterior, seria algo como:

```python
await User.drop_indexes()
```

!!! Danger
    Executar o `drop_indexes()` excluirá **todos os índices** do documento declarado, portanto, cuidado e tenha absoluta certeza de que está a executar a operação com cuidado.

#### Excluir índices individuais

E se quiser excluir manualmente apenas um índice? Bem, isso também é possível chamando `drop_index()`.

A sintaxe é muito clara e simples:

```python
await MyDocument.drop_index(<NOME-DO-ÍNDICE>)
```

Por exemplo, usando o documento `User` anterior, onde o `name` era um índice, seria algo como:

```python
await User.drop_index("name")
```

!!! Warning
    Se tentar excluir um índice com um nome de campo não declarado no documento ou não declarado como índice, pelo menos, um `InvalidKeyError` será lançado.

#### Verificações do documento

Se também deseja garantir que executa as verificações adequadas para os índices, por exemplo, se um índice foi excluído do documento e deseja garantir que isso seja refletido, também é possível faze-lo.

A sintaxe é muito clara e simples:

```python
await MyDocument.check_indexes()
```

Por exemplo:

```python
await User.check_indexes()
```

Isto pode ser útil se quiser garantir que, para cada [registry](./registry.md), todos os documentos tenham os índices verificados antecipadamente.

#### Criar índices para várias bases de dados

E se você tiver o mesmo documento em várias bases de dados (multi-tenancy, por exemplo) e quiser refletir os índices em todo o lado? O Mongoz também oferece essa opção.

Os nomes das bases de dados devem ser passados como uma lista ou tuplo de strings.

A sintaxe é muito simples:

```python
await MyDocument.create_indexes_for_multiple_databases(["db_um", "db_dois", "db_tres"])
```

Por exemplo:

```python
await User.create_indexes_for_multiple_databases(["db_um", "db_dois", "db_tres"])
```

#### Excluir índices para várias bases de dados

E se você tiver o mesmo documento em várias bases de dados (multilocação, por exemplo) e quiser excluir os índices todo o lado? O Mongoz também oferece essa opção.

Os nomes das bases de dados devem ser passados como uma lista ou tuplo de strings.

A sintaxe é muito simples:

```python
await MyDocument.drop_indexes_for_multiple_databases(["db_um", "db_dois", "db_tres"])
```

Por exemplo:

```python
await User.drop_indexes_for_multiple_databases(["db_um", "db_dois", "db_tres"])
```

[edgy]: https://edgy.tarsild.io
