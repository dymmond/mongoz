# Managers

Os gestores são uma ótima ferramenta que o **Mongoz** oferece. Fortemente inspirados pelo [Edgy](https://edgy.tarsild.io), os gestores permitem que construa pesquisas personalizadas prontas para serem usadas pelos documentos.

O **Mongoz** por defeito usa o gestor chamado `objects`, o que torna simples de perceber.

Vamos ver um exemplo.

```python
{!> ../../../docs_src/managers/simple.py !}
```

Ao consultar a tabela `User`, o `objects` (gestor) é o padrão e **deve** estar sempre presente ao fazê-lo.

!!! Danger
    Isto aplica-se apenas ao lado do `manager` do Mongoz, por exemplo, ao usar `Document.objects....`. **Ao usar `Document.query...` isto não funcionará**.

### Gestor personalizado

Também é possível ter os próprios gestores personalizados e para fazer isso, **deve herdar**
a classe **QuerySetManager** e substituir o `get_queryset()`.

Para aqueles familiarizados com os gestores do Django, o princípio é exatamente o mesmo. 😀

**Os gestores devem ser anotados como ClassVar** ou um erro será lançado.

```python
{!> ../../../docs_src/managers/example.py !}
```

Agora vamos criar um novo gestor e usá-lo com nosso exemplo anterior.

```python
{!> ../../../docs_src/managers/custom.py !}
```

Estes gestores podem ser tão complexos quanto desejar, com quantos filtros desejar. O que precisa fazer é
simplesmente substituir o `get_queryset()` e adicioná-lo aos seus documentos.

### Substituir o gestor padrão

Também é possível substituir o gestor padrão criando o gestor personalizado e substituindo
o gestor `objects`.

```python
{!> ../../../docs_src/managers/override.py !}
```

!!! Warning
    Tenha cuidado ao substituir o gestor padrão, pois pode não obter todos os resultados do
    `.all()` se não filtrar correctamente.
