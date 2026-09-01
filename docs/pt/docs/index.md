# MongoZ

<p align="center">
  <a href="https://mongoz.dymmond.com"><img src="https://res.cloudinary.com/tarsild/image/upload/v1695724284/packages/mongoz/nwtcudxmncgoyw4em0th.png" alt='mongoz'></a>
</p>

<p align="center">
    <em>🔥 ODM com Pydantic simpificado 🔥</em>
</p>

<p align="center">
<a href="https://github.com/dymmond/mongoz/actions/workflows/test-suite.yml/badge.svg?event=push&branch=main" target="_blank">
    <img src="https://github.com/dymmond/mongoz/actions/workflows/test-suite.yml/badge.svg?event=push&branch=main" alt="Test Suite">
</a>

<a href="https://pypi.org/project/mongoz" target="_blank">
    <img src="https://img.shields.io/pypi/v/mongoz?color=%2334D058&label=pypi%20package" alt="Package version">
</a>

<a href="https://pypi.org/project/mongoz" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/mongoz.svg?color=%2334D058" alt="Supported Python versions">
</a>
</p>

---

**Documentação**: [https://mongoz.dymmond.com][mongoz] 📚

**Código Fonte**: [https://github.com/dymmond/mongoz](https://github.com/dymmond/mongoz)

---

## Motivação

MongoZ é um ODM (Object Document Mapper) assíncrono para MongoDB em Python, construído sobre o [PyMongo Async][pymongo] nativo e o [Pydantic][pydantic].

MongoZ também é inspirado no excelente trabalho do [Aminalee](https://aminalaee.dev/mongox/) com o MongoX.

Então, o porquê de um MongoZ se já existe o MongoX? Bem, o MongoZ é do mesmo autor do [Esmerald][esmerald], [Saffier][saffier], e muitas outras ferramentas, e todas elas seguem uma necessidade e padrão específicos de desenvolvimento.

O Mongox implementa muito bem algumas operações com o MongoDB, mas para casos de uso onde são necessários [Signals](./signals.md), por exemplo, o Mongox não foi desenhado para tal. Além disso, como o criador do Mongoz é o mesmo do [Saffier][saffier] e do [Edgy][edgy], a interface amigável para interação com o ODM também é essencial.

No final, havia a necessidade de adicionar o Pydantic 2+ com alguns extras que não estavam presentes no Mongox.

## MongoZ

Este é uma espécie de fork do Mongox com um *core* reescrito, mas reutilizando algumas das suas melhores funcionalidades, ao mesmo tempo em que adiciona recursos adicionais e uma interface comum e amigável, para além de intuitiva.

Este ODM é desenhado para ser **assíncrono**, o que significa flexibilidade e compatibilidade com várias frameworks disponíveis, como [Esmerald][esmerald], FastAPI, Sanic, Starlette, Lilya e muitas outras, tornando o MongoZ **independente de qualquer framework**.


## Funcionalidades

Ao adoptar uma interface mais familiar, este também oferece recursos interessantes e poderosos usando o Pydantic e o PyMongo Async.

### Sintaxe

**Mongoz permite o uso de dois tipos diferentes de sintaxe**.

* Com uma interface familiar inspirada no [Edgy][edgy].
* Com uma interface familiar inspirada no Mongox.

**A documentação segue uma interface mais familiar inspirada no [Edgy][edgy], mas também mostrará**
**como pode usar a outra sintaxe também permitida**.

### Principais recursos

* **Herança de documentos** - Para casos em que não quer repetir informações, mantendo a integridade dos documentos.
* **Classes abstratas** - Isso mesmo! Às vezes só quer um documento que contenha campos comuns e que não precise ser criado como um documento na base de dados.
* **Classes Meta** - Se está familiarizado com o Django, isto não é novidade e o Mongoz oferece isso da mesma forma.
* **Filtros** - Filtrar por qualquer campo que queira e precise.
* **Operadores de modelo** - Operações clássicas como `update`, `get`, `get_or_none` e muitas outras.
* **Índices** - Índices únicos através dos meta campos.
* **Sinais** - Recurso bastante útil se você quiser "ouvir" o que está a acontecer com os documentos.

E muito mais pode-se fazer aqui.

## Instalação

Para instalar o Mongoz, execute:

```shell
$ pip install mongoz
```


## Início Rápido

O seguinte é um exemplo de como começar com o Mongoz e mais detalhes e exemplos podem ser encontrados ao longo da documentação.

Utilize o `ipython` para executar o seguinte a partir da consola, uma vez que suporta `await`.

```python
{!> ../../../docs_src/quickstart/quickstart.py !}
```

Agora pode gerar alguns documentos e inseri-los na base de dados.

=== "Simples"

    ```python
    user = await User.objects.create(name="Mongoz", email="mongoz@mongoz.com")
    ```

=== "Alternativa"

    ```python
    user = await User(name="Mongoz", email="mongoz@mongoz.com").create()
    ```

Isso retornará uma instância de um `User` num modelo Pydantic e o `mypy` entenderá automaticamente que esta é uma instância de `User`, o que significa que os tipos e validações funcionarão em todo o lado.

### Pesquisar

O Mongoz utiliza o PyMongo Async e oferece padrões de pesquisa familiares ao PyMongo através da sua API assíncrona.

=== "Simples"

    ```python
    user = await User.objects.get(name="Mongoz")
    ```

=== "Alternativa"

    ```python
    user = await User.query({"name": "Mongoz"}).get()
    ```

Ou pode usar os campos do `User` em vez de dicionários (**seleccione a opção "Alternativa" para esta opção**).

=== "Simples"

    ```python
    user = await User.objects.get(name="Mongoz")
    ```

=== "Alternativa"

    ```python
    user = await User.query({User.name: "Mongoz"}).get()
    ```

Ou uma abordagem mais semelhante ao Python (**seleccione a opção "Alternativa" para esta opção**).

=== "Simples"

    ```python
    user = await User.objects.get(name="Mongoz")
    ```

=== "Alternativa"

    ```python
    user = await User.query(User.name == "Mongoz").get()
    ```

Existem muitas operações que pode fazer com o Mongoz e pode vê-las todas ao longo da documentação ou na secção [Queries](./queries.md).

**Mongoz** valoriza a simplicidade e não há preferência na sintaxe usada nas pesquisas.
Pode usar o que chamamos de opção "Mongoz" e a opção "Alternativa" ao mesmo tempo, pois ambas funcionam muito bem em comum.

**Ambas são sintaxes do Mongoz, mas para fins de representação, classificamos com nomes diferentes na documentação**.

## Observação

A declaração de documentos do Mongoz com tipagem é meramente visual. As validações dos campos não são feitas pela tipagem do atributo dos documentos, mas sim pelos campos do Mongoz.

Isso significa que não precisa se preocupar com a tipagem errada, desde que declare o tipo de campo correcto.

Então isso significa que o Pydantic não funcionará se não declarar o tipo? Claramente que não.
Internamente, o Mongoz executa essas validações por meio dos campos declarados e as validações do Pydantic são feitas exatamente da mesma forma que faria num modelo Pydantic normal.

Nada com que se preocupar!

[mongoz]: https://mongoz.dymmond.com
[pymongo]: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/
[pydantic]: https://pydantic.dev/
[mongoz]: https://mongoz.dymmond.com
[saffier]: https://saffier.tarsild.io
[edgy]: https://edgy.tarsild.io
[esmerald]: https://esmerald.dev
