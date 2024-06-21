# Truques e Dicas

Esta parte é dedicada à organização de código dentro da aplicação.

Os exemplos estão mais focados no [Esmerald](https://esmerald.dev) já que o autor é o mesmo, mas novamente, pode fazer o mesmo na sua framework preferida.

## Colocar a sua conecção num local centralizado

Provavelmente isto é o que gostaria de fazer na sua aplicação, uma vez que não quer declarar repetidamente as mesmas variáveis.

A principal razão para isto é o facto de que cada vez que se declara um [registo](./registry.md), na verdade está a criar um novo objeto e isso não é ideal se precisar de aceder aos documentos utilizados no registo principal, certo?

### Colocar os detalhes da conecçâo dentro de um ficheiro de configurações global

Esta é provavelmente a forma mais fácil de colocar os detalhes da conecção, especialmente para o Esmerald, já que possui uma maneira simples e fácil de acessar as configurações em qualquer parte do código.

Algo simples como isto:

```python hl_lines="18-25"
{!> ../../../docs_src/tips/settings.py !}
```

Como pode ver, agora tem a `db_connection` num único local e de fácil acesso em qualquer parte do
seu código. No caso do Esmerald:

```python hl_lines="3"
from esmerald.conf import settings

registry = settings.db_connection
```

**Mas isso é suficiente?** Não.

Como mencionado anteriormente, ao atribuir ou criar uma variável, o próprio Python gera um novo objeto com um `id` diferente,
que pode ser diferente a cada vez que precisa importar as configurações nos locais necessários.

Não vamos falar sobre este truque, visto que há muita documentação online e mais adequada para este mesmo propósito.

Como resolvemos este problema? Entra em cena o [lru_cache](#a-lru-cache).

## A LRU cache

LRU extends significa **least recently used**.

Uma técnica muito comum que visa ajudar a fazer cache de certas partes de funcionalidade dentro do código e garantir
que **não cria** objetos extras, e é exatamente isso que precisamos.

Usando o exemplo acima, vamos agora criar um novo ficheiro chamado `utils.py`, onde aplicaremos a técnica `lru_cache` para a nossa `db_connection`.

```python title="utils.py" hl_lines="6"
{!> ../../../docs_src/tips/lru.py !}
```

Isto garantirá que a partir de agora irá usar sempre a mesma conecção e registro dentro da aplicação, importando o `get_db_connection()` sempre que for necessário.

## Exemplo prático

Para este exemplo, teremos a seguinte estrutura (não iremos usar todos os ficheiros).
Não iremos criar *views* visto que este não é o propósito do exemplo.

```shell
.
└── myproject
    ├── __init__.py
    ├── apps
    │   ├── __init__.py
    │   └── accounts
    │       ├── __init__.py
    │       ├── tests.py
    │       └── v1
    │           ├── __init__.py
    │           ├── schemas.py
    │           ├── urls.py
    │           └── views.py
    ├── configs
    │   ├── __init__.py
    │   ├── development
    │   │   ├── __init__.py
    │   │   └── settings.py
    │   ├── settings.py
    │   └── testing
    │       ├── __init__.py
    │       └── settings.py
    ├── main.py
    ├── serve.py
    ├── utils.py
    ├── tests
    │   ├── __init__.py
    │   └── test_app.py
    └── urls.py
```
Esta estrutura é gerada utilizando as
[directivas Esmerald](https://esmerald.dev/directives/directives/)

### As configurações

Como mencionado anteriormente, teremos um ficheiro de configurações com as propriedades de ligação à base de dados montadas.

```python title="my_project/configs/settings.py" hl_lines="18-19"
{!> ../../../docs_src/tips/settings.py !}
```

### Os utilitários

Agora criamos o `utils.py` onde aplicamos a técnica [LRU](#a-lru-cache).

```python title="myproject/utils.py" hl_lines="6"
{!> ../../../docs_src/tips/lru.py !}
```

### Os documentos

Agora podemos começar a criar os nossos [documentos](./documents.md) e garantir que os mantemos sempre no mesmo [registo](./registry.md).

```python title="myproject/apps/accounts/documents.py" hl_lines="7 12-14"
{!> ../../../docs_src/tips/models.py !}
```

Aqui aplicamos a [herança](./documents.md#com-herança) para torná-lo mais limpo e legível
caso queiramos ainda mais documentos.

Como também pode notar, estamos a importar o `get_db_connection()` previamente criado. Agora é
o que usaremos em todos os lugares.

## Notas

O [exemplo](#exemplo-prático) acima mostra como pode aproveitar local centralizado para gerir suas conecções e usá-las em toda a aplicação,
mantendo o código sempre limpo, não redundante e bonito.

Este exemplo pode ser aplicado a qualquer uma das frameworks preferidas e pode usar tantas técnicas diferentes
quanto achar adequado para o seu propósito.

**Mongoz é independente de qualquer framework**.
