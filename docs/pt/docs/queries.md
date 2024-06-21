# Queries

Fazer pesquisas é essencial para utilizar um ODM e poder fazer pesquisas complexas é ainda melhor quando assim o é permitido.

O MongoDB é conhecido pela sua performance ao pesquisas uma base de dados e é muito rápido nisso.

Ao fazer pesquisas num [documento][document], o ODM permite duas maneiras diferentes de pesquisa. Uma é utilizando o **manager** interno e a segunda é utilizando o **queryset**.

Na realidade, o `manager` e o `queryset` são muito parecidos, mas para fins internos, foi decidido chamá-los desta maneira para deixar claro como as pesquisas podem ser feitas.

Se ainda não viu a seção de [documentos][document], agora seria uma ótima altura para dar uma vista de olhos e se familiarizar.

Para fins desta documentação, mostraremos como fazer pesquisas utilizando tanto o `manager` quanto o `queryset`.

Tanto o queryset quanto o manager funcionam muito bem quando combinados. No final, cabe ao programador decidir qual prefere.

## Manager and QuerySet

Quando se faz pesquisas dentro do Mongoz, isto retorna um objeto se deseja apenas um resultado ou um `queryset`/`manager` que é a representação interna de varios resultados.

Se está familiarizado com as querysets do Django, isto é **quase** a mesma coisa e por quase é porque o mongoz restringe as atribuições de variáveis da queryset de forma mais livre.

Vamos nos familiarizar com as pesquisas.

Vamos supor que tenha o seguinte documento `User` definido.

```python
{!> ../../../docs_src/queries/document.py !}
```

Como mencionado anteriormente, o Mongoz permite usar duas formas de pesquisa. Através do `manager` e do `queryset`.
Ambos permitem chamadas encadeadas, por exemplo, `sort()` com um `limit()` combinado.

Por exemplo, vamos criar um utilizador.

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

Como pode verificar, o **manager** utiliza `objects` para aceder às operações e o `queryset` faz de forma diferente.

Para aqueles familiarizados com o Django, o `manager` segue a mesma linha.

Agora vamos fazer uma pesquisa à base de dados para obter um registro simples, filtrando-o por `email` e `first_name`.
Queremos que isto retorne uma lista, já que estamos a utilizar um `filter`.

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

Bastante simples, certo? Bem sim, embora preferencialmente recomendemos o uso do `manager` para quase tudo o que pode fazer com o Mongoz,
às vezes usar o `queryset` também pode ser útil se gosta de sintaxes diferentes. Esta sintaxe foi inspirada no Mongox.

## Retornando managers/querysets

Existem muitas operações que pode fazer com os managers/querysets e depois também pode aproveitar essas mesmas para seus casos de uso.

Os seguintes operadores retornam `managers`/`querysets`, o que significa que você pode combinar diferentes operadores ao mesmo tempo.

Isso também significa que você pode aninhar vários tipos diferentes e iguais. Por exemplo:

```python
await User.objects.filter(...).sort(...).filter(...).limit(2)
```

Todas as operações que retornam managers e querysets permitem chamadas combinadas/aninhadas.

### Filter

O `filtro` é exclusivo do `manager` e não existe desta forma no `queryset`.
A versão do `queryset` é a [Query](#query).

#### Django-style

Estes filtros são as mesmas pesquisas no estilo **Django**.

```python
users = await User.objects.filter(is_active=True, email__icontains="gmail")
```

Os mesmos operadores especiais também são adicionados automaticamente em cada coluna.

* **in** - O operador `IN`.
* **not_in** - O oposto de `in`, ou seja, todos os registos que não estão na condição.
* **contains** - Filtrar instâncias que contêm um valor específico.
* **icontains** - Filtrar instâncias que contêm um valor específico, sem distinguir maiúsculas de minúsculas.
* **lt** - Filtrar instâncias com valores "Menor Que".
* **lte** - Filtrar instâncias com valores "Menor or Igual Que".
* **gt** - Filtrar instâncias com valores "Maior Que".
* **gte** - Filtrar instâncias com valores "Maior ou Iugal Que".
* **asc** - Filtrar instâncias por ordem ascendente quando `_asc=True`.
* **desc** - Filtrar instâncias por ordem descendente quando `_desc=True`.
* **neq** - Filtrar instâncias por não ser igual à condição.

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
users = await User.objects.filter(id__asc=False) # mesmo que desc True
users = await User.objects.filter(id__desc=True)
users = await User.objects.filter(id__desc=False) # mesmo que asc True
users = await User.objects.filter(id__neq=1) # memso que asc True
```

### Using

Alterar a base de dados durante a consulta, apenas precisa fornecer o nome para alterar a base de dados de destino.

=== "Manager"

    ```python
    users = await User.objects.using("my_mongo_db").all()
    ```

### Query

A `query` é o que é usado pelo `queryset` em vez do `manager`. Noutras palavras, a `query` é para o `queryset` o que o `filter` é para o `manager`.

Um exemplo de query seria:

```python
users = await User.query(User.email == "mongoz@mongoz.com").query(User.id > 1).all()
```

Ou, alternativamente, pode usar dicionários.

```python
user = await User.query({"first_name": "Mongoz"}).all()
```

Ou pode usar os campos do `User` em vez de dicionários.

```python
user = await User.query({User.first_name: "Mongoz"}).all()
```

### Limit

Limitar o número de resultados.

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

Saltar (ignorar) um certo número de documentos.

=== "Manager"

    ```python
    users = await User.objects.filter(email__icontains="mongo").skip(1)
    ```

=== "QuerySet"

    ```python
    users = await User.query().skip(1)
    ```

### Raw

Executar pesquisas em "bruto" diretamente. Isto permite ter algum tipo de controlo sobre pesquisas mais complicadas que pode encontrar.

#### Consultas simples e aninhadas em bruto

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

#### Complexo com sintaxe específica do MongoDB

E se quiser evoluir e adicionar extras?

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

Ordenar os valores com base nas chaves. A ordenação, assim como qualquer retorno do manager/queryset, permite chamadas aninhadas.

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

O operador [Q](#o-operador-q) também permite algumas combinações se optar por esta mesma sintaxe.

Agora, é possível combinar a sintaxe do sort do `queryset` com a sintaxe do sort do `manager`? **Sim, é possível**. Um exemplo seria algo como isto:

```python
users = await User.objects.sort(Q.desc(User.name)).sort(Q.asc(User.email)).all()
```

!!! Danger
    A sintaxe do `queryset` é permitida dentro do `manager`, **mas não o contrário**.

### None

Se apenas precisar retornar um manager ou queryset vazio.

=== "Manager"

    ```python
    manager = await User.objects.none()
    ```

=== "QuerySet"

    ```python
    queryset = await User.query().none()
    ```

## Returning results

Estas são as operações que retornam resultados em vez de *managers* ou *querysets*. O que significa que não é possível aninhá-las.

### All

Retorna todas as intâncias-

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

Esta é uma operação clássica que é muito útil dependendo das operações que precisa realizar.
Usado para guardar um objeto existente na base de dados. Um pouco diferente do [update](#update) e
mais simples de ler.

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

Agora, um cenário mais único, mas possível, com um save. Imagine que precisa criar uma cópia exata de um objeto e guardá-lo na base de dados.
Estes casos são mais comuns do que imagina, mas este exemplo é apenas para fins ilustrativos.

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

Usado para eliminar uma instância.

=== "Manager"

    ```python
    await User.objects.filter(email="foo@bar.com").delete()
    ```

=== "QuerySet"

    ```python
    await Movie.query({User.email: "foo@bar.com"}).delete()
    ```

Ou diretamente na instância.

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

Pode atualizar instâncias de documentos chamando este operador.

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

Também existe a possibilidade de atualizar todos os registos com base numa pesquisa específica.

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

Obtém um único registo da base de dados.

=== "Manager"

    ```python
    user = await User.objects.get(email="foo@bar.com", name="Mongoz")
    ```

=== "QuerySet"

    ```python
    user = await User.query(User.email == "foo@bar.com").query(User.name == "Mongoz").get()
    ```

Também é possível combinar os resultados do queryset com este operador.

=== "Manager"

    ```python
    user = await User.objects.filter(email="foo@bar.com").get()
    ```

=== "QuerySet"

    ```python
    user = await User.query().query(User.email == "foo@bar.com").get()
    ```

### First

Quando precisar retornar o primeiro resultado de um queryset.

=== "Manager"

    ```python
    user = await User.objects.first()
    ```

=== "QuerySet"

    ```python
    user = await User.query().first()
    ```

Também é possível aplicar filtros quando necessário.

=== "Manager"

    ```python
    user = await User.objects.filter(email="foo@bar.com").first()
    ```

=== "QuerySet"

    ```python
    user = await User.query(User.email == "foo@bar.com").first()
    ```

### Last

Quando precisar retornar o último resultado de um queryset.

=== "Manager"

    ```python
    user = await User.objects.last()
    ```

=== "QuerySet"

    ```python
    user = await User.query().last()
    ```

Também é possível aplicar filtros quando necessário.

=== "Manager"

    ```python
    user = await User.objects.filter(name="mongoz").last()
    ```

=== "QuerySet"

    ```python
    user = await User.query(User.email == "mongoz").last()
    ```

### Count

Retorna um número inteiro com o total de registos.

=== "Manager"

    ```python
    total = await User.objects.count()
    ```

=== "QuerySet"

    ```python
    total = await User.query().count()
    ```

### Exclude

O `exclude()` é usado quando deseja filtrar os resultados excluindo instâncias.

=== "Manager"

    ```python
    users = await User.objects.exclude(is_active=False)
    ```

=== "QuerySet"

    ```python
    users = await User.query(Q.not_(User.is_active, False)).all()
    ```

    Com o queryset, simplesmente chamamos o operador [Not](#not).

### Values

Retorna os resultados do modelo num formato de dicionário.

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

O `values()` também pode ser combinado com `filter`, `only` como de costume.

**Parâmetros**:

* **fields** - Campos a retornar.
* **exclude** - Campos a excluir do retorno.
* **exclude_none** - Sinalizador booleano indicando se os campos com `None` devem ser excluídos.

### Values list

Retorna os resultados do modelo nm formato de tuplo.

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

O método `values_list()` também pode ser combinado com `filter`, `only` como de costume.

**Parâmetros**:

* **fields** - Campos a retornar.
* **exclude** - Campos a excluir do retorno.
* **exclude_none** - Sinalizador booleano indicando se os campos com `None` devem ser excluídos.
* **flat** - Sinalizador booleano indicando se os resultados devem ser achatados.

### Only

Retorna os resultados contendo **apenas** os campos na pesquisa e nada mais.

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
    Só pode utilizar `only()` ou `defer()`, mas não ambos combinados, caso contrário, será lançado um `FieldDefinitionError`.

### Defer

Retorna os resultados contendo todos os campos **excepto aqueles que deseja excluir**.

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
    Só pode utilizar `only()` ou `defer()`, mas não ambos combinados, caso contrário, será lançado um `FieldDefinitionError`.

### Get or none

Ao pesquisar um documento e não desejar obter um [DocumentNotFound](./exceptions.md#documentnotfound) e, em vez disso, retornar `None`.

=== "Manager"

    ```python
    user = await User.objects.get_or_none(id=1)
    ```

=== "QuerySet"

    ```python
    user = await User.query(User.id == 1).get_or_none()
    ```

### Where

Aplicar pesquisas de strings em bruto ou a cláusula `where`.

=== "Manager"

    ```python
    user = await User.objects.where("this.email == 'foo@bar.com'")
    ```

=== "QuerySet"

    ```python
    user = await User.query().where("this.email == 'foo@bar.com'")
    ```

### Distinct values

Filtrar por valores distintos e retornar uma lista desses mesmos valores.

=== "Manager"

    ```python
    user = await User.objects.distinct_values("email")
    ```

=== "QuerySet"

    ```python
    user = await User.query().distinct_values("email")
    ```

### Get document by id

Obter um documento pelo `_id`. Esta funcionalidade aceita o parâmetro `id` como uma string ou `bson.ObjectId`.

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

## Métodos úteis

### Get or create

Quando precisar obter uma instância existente de um documento a partir de uma consulta correspondente. Se existir, retorna ou cria uma nova caso não exista.

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

Isto irá pesquisar o documento `User` com o `email` como chave de pesquisa. Se não existir, então irá utilizar esse valor com os `defaults` fornecidos para criar uma nova instância.

### Bulk create

Quando precisar criar várias instâncias de uma só vez, ou `em massa`.

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

Quando precisar atualizar várias instâncias de uma só vez, ou `em massa`.

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

## Nota

Quando aplicar as funções que retornam valores diretamente e não managers ou querysets,
**ainda é possível aplicar os operadores como `filter`, `skip`, `sort`...**

## Consultar documentos incorporados

Consultar [documentos incorporados](./embedded-documents.md) também é fácil e aqui o `queryset` é muito poderoso para fazê-lo.

Vamos ver um exemplo.

```python hl_lines="17"
{!> ../../../docs_src/queries/embed.py !}
```

Agora podemos criar algumas instâncias do `User`.

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

Isto irá criar o seguinte documento na base de dados:

```json
{
    "email": "mongoz@mongoz.com", "first_name": "Mongoz", "last_name": "ODM",
    "is_active": true, "access_level": {"level": "admin" }
},
```

Agora é possível pesquisar o utilizador pelo campo do documento incorporado.

```python
await User.query(User.user_type.level == "admin").get()
```

Este é o equivalente ao seguinte filtro:

```json
{"access_level.level": "admin" }
```

Também pode utilizar o documento incorporado completo.

```python
await User.query(User.user_type == level).get()
```

Este é o equivalente ao seguinte filtro:

```json
{"access_level": {"level": "admin"} }
```

!!! Warning
    Para o tipo de pesquisa [Documentos Incorporados](./embedded-documents.md), usando o manager não irá funcionar.
    **Deve-se usar a abordagem do tipo `queryset` para a pesquisa**.

## O operador Q

Este operador foi inspirado pelo `Mongox` e estendido para as necessidades do Mongoz. O crédito pelo design inicial do operador `Q` vai para o `Mongox`.

A classe `Q` contém alguns métodos úteis e bastante práticos para serem usados nas pesquisas.

```python
from mongoz import Q, Order
```

O operador `Q` é principalmente usado no `queryset` e não tanto no `manager`, e a principal razão para isso é porque o `manager` manipula internamente o operador `Q` automaticamente. Bem porreiro, não é?

Para criar, por exemplo, uma pesquisa de `sort`, normalmente faria assim:

```python
users = await User.query().sort(User.email, Order.DESCENDING).all()
```

Onde é que o operador `Q` entra aqui? Bem, pode ser visto como um atalho para as suas pesquisas.

### Ascending

```python
users = await User.query().sort(Q.asc(User.email)).all()
```

### Descending

```python
users = await User.query().sort(Q.desc(User.email)).all()
```

### In

O operados `in`.

```python
users = await User.query(Q.in_(User.id, [1, 2, 3, 4])).all()
```

### Not In

O operador `not_in`.

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

### Padrão

Aplica alguns padrões `$regex`.

```python
users = await User.query(Q.pattern(User.email, r"\w+ foo \w+")).all()
```

### Igual

O operador `equals`.

```python
users = await User.query(Q.eq(User.email, "foo@bar.com")).all()
```

### Diferente

O operador `not equals`.

```python
users = await User.query(Q.neq(User.email, "foo@bar.com")).all()
```

### Where

Aplicando o operador `where` do MongoDB.

```python
users = await User.query(Q.where(User.email, "foo@bar.com")).all()
```

### Maior do que

```python
users = await User.query(Q.gt(User.id, 1)).all()
```

### Maior ou Igual que

```python
users = await User.query(Q.gte(User.id, 1)).all()
```

### Menor do que

```python
users = await User.query(Q.lt(User.id, 20)).all()
```

### Menor ou Igual que

```python
users = await User.query(Q.lte(User.id, 20)).all()
```

## Queries *blocking*

O que acontece se você quiser usar o Mongoz com uma operação *blocking*? Por *blocking*, entende-se "síncrono".
Por exemplo, o Flask não suporta nativamente operações "assíncronas" e o Mongoz é um ODM assíncrono agnóstico e
provavelmente gostaria de aproveitar o Mongoz, mas sem fazer muita magia nos bastidores.

Bem, o Mongoz também suporta a funcionalidade `run_sync` que permite executar as consultas em modo
*blocking* com facilidade!

### Como utilizar

Simplesmente precisa utilizar a funcionalidade `run_sync` do Mongoz e torná-la quase imediata.

```python
from mongoz import run_sync
```

Todas as funcionalidades disponíveis do Mongoz são executadas dentro deste invólucro sem sintaxe extra.

Vejamos alguns exemplos.

**Modo async**

```python
await User.objects.all()
await User.objects.filter(name__icontains="example")
await User.objects.create(name="Mongoz")
```

**Com run_sync**

```python
from mongoz import run_sync

run_sync(User.objects.filter(name__icontains="example"))
run_sync(User.objects.create(name="Mongoz"))
```

[document]: ./documents.md
