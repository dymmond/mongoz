# Documentos incorporados

Documentos incorporados são documentos que são incorporados no `mongoz.Document`. A diferença entre um e
outro é que o `EmbeddedDocument` não é inserido separadamente e não possui um `_id` separado.

Para definir um `EmbeddedDocument`, deve herdar de `mongoz.EmbeddedDocument` e definir os
[campos](./fields.md) da mesma forma que definiria para qualquer outro `mongoz.Document`.

```python hl_lines="4 10 14-15 19 23 28 30-31"
{!> ../../../docs_src/documents/embed.py !}
```

Como pode ver, o `EmbeddedDocument` não é um documento independente em si, mas parte do
[documento](./documents.md) ao declarar.

Um `EmbeddedDocument` pode ser usado dentro de outro e, portanto, criar uma declaração *nested*
ao guardar os resultados.
