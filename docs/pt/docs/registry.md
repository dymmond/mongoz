# Registo

Ao utilizar o **Mongoz**, é necessário utilizar o objeto **Registo** para indicar exatamente onde a base de dados será escrita.

Imagine o registo como um mapeamento entre os seus documentos e a base de dados onde serão escritos.

E é apenas isso, nada mais, um objeto muito simples mas eficaz.

O registo também é o objeto que pode ser utilizado ao gerar migrações utilizando o Alembic.

```python hl_lines="19"
{!> ../../../docs_src/registry/model.py !}
```

## Parâmetros

* **url** - O URL da base de dados para se conectar.

    ```python
    from mongoz import Registo

    registo = Registo(url="mongodb://localhost:27017")
    ```

## Ciclo de vida do cliente

Cada `Registry` cria e possui exatamente um `AsyncMongoClient` do PyMongo. As bases de dados e
coleções obtidas através do registo reutilizam esse cliente. O registo fica associado ao ciclo de
eventos da primeira operação e não deve ser partilhado com outro ciclo de eventos.

Execute `await registry.close()` durante o encerramento da aplicação. O encerramento é idempotente
e definitivo; um registo fechado não cria outro cliente. Para trabalho delimitado, também pode usar
`async with Registry(...) as registry`.

## Registo personalizado

É possível ter o seu próprio Registo personalizado? Sim, claro! Basta criar uma subclasse da classe `Registry` e continuar a partir daí, como qualquer outra classe Python.

```python
{!> ../../../docs_src/registry/custom_registry.py !}
```

## Executar algumas verificações de documentos

Por vezes, pode ser útil garantir que todos os documentos têm os índices atualizados antecipadamente. Isso pode ser especialmente útil se já tiver um documento e alguns índices foram atualizados, adicionados ou removidos. Esta funcionalidade executa essas verificações para todos os documentos do registo fornecido.

```python
{!> ../../../docs_src/registry/document_checks.py !}
```

### Utilização numa framework

Esta funcionalidade também pode ser útil se estiver a utilizar, por exemplo, uma framework ASGI como o Starlette, [Lilya](https://lilya.dev) ou [Esmerald](https://esmerald.dev).

Estas frameworks tratam do ciclo de vida do evento para si e é aqui que deseja garantir que essas verificações são executadas antecipadamente.
O mesmo ciclo de vida da aplicação deve fechar o registo durante o encerramento.

Como o Mongoz é da mesma equipa que o [Lilya](https://lilya.dev) e o [Esmerald](https://esmerald.dev), vamos ver como ficaria com o Esmerald.

```python
{!> ../../../docs_src/registry/asgi_fw.py !}
```
