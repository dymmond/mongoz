# Desempenho, segurança e resiliência em produção

Este guia define a fronteira operacional entre Mongoz, PyMongo/MongoDB e a aplicação. Topologia,
rede, índices e dados normalmente dominam a latência observada pela aplicação.

## Cliente e segredos

Crie um `Registry` por ciclo de vida da aplicação e reutilize-o. O Registry possui um único
`AsyncMongoClient` e deve ser fechado no mesmo event loop durante o encerramento. Carregue a URI do
MongoDB a partir de um gestor de segredos. Não coloque credenciais em código, argumentos de linha de
comandos, logs ou atributos de monitorização. `registry.url` mantém a URI por compatibilidade e não
deve ser registado em logs.

## Timeouts, retries e concerns

O Mongoz passa a URI completa ao PyMongo sem criar outra camada de timeout. Configure
`serverSelectionTimeoutMS`, `connectTimeoutMS`, `socketTimeoutMS`, `waitQueueTimeoutMS` e
`timeoutMS` como opções nativas. Para um orçamento local use `pymongo.timeout(...)`.

Retries, read preference, read concern e write concern também pertencem ao PyMongo. Exceções de
seleção de servidor, timeout, chave duplicada, bulk parcial, write concern e transação preservam os
tipos nativos. A aplicação decide quando uma operação composta é idempotente e pode ser repetida.

## Cancelamento e recuperação

O Mongoz não traduz `asyncio.CancelledError`. Cursores são fechados na conclusão, falha,
cancelamento e fecho explícito. Se a limpeza do contexto do Registry também falhar, a exceção
original permanece principal e a falha de limpeza é encadeada. Um Registry aberto continua
reutilizável depois de uma operação falhada quando o PyMongo o permite; um Registry fechado é final.

Sessões e transações pertencem ao PyMongo e devem ser usadas sequencialmente. Signals são aguardados
em ordem, sem tarefas em background; uma falha de receiver pode acontecer depois de a escrita já ter
terminado, por isso não repita a escrita automaticamente.

## Resultados grandes

`all()`, `values()`, `values_list()`, `where()`, agregação de alto nível e updates que devolvem listas
materializam resultados. Use iteração assíncrona para leituras grandes. Ao interromper e reter um
iterador, feche-o explicitamente com `await iterator.aclose()`. Para controlar batches use o cursor
nativo, por exemplo `User.get_collection().driver.find(...).batch_size(100)`. Para updates amplos
sem modelos de retorno, prefira `update_many()` ou `bulk_write()` nativos.

## Fronteiras de confiança

Persistência modelada escreve apenas campos declarados. Dicionários raw, argumentos em dicionário de
`query()`, `Expression`, pipelines, bulk writes, padrões regex e acesso nativo são interfaces para
código confiável; nunca encaminhe estruturas de pedidos diretamente. `read_only` é metadado de campo,
não autorização de pedidos.

`contains`, `icontains`, `startswith` e `endswith` tratam metacarateres como texto literal.
`Q.pattern()` é a interface regex explícita. `$where` executa JavaScript no servidor, foi
descontinuado no MongoDB 8.0 e deve ser substituído por operadores normais ou `$expr`.

PyMongo/MongoDB controlam tipos BSON, tamanho máximo de documentos e limites do servidor. A aplicação
deve limitar tamanho e profundidade dos pedidos antes de construir modelos.

## Observabilidade e desempenho

Use command monitoring do PyMongo com redacção apropriada; não crie etiquetas com URIs completas.
Os microbenchmarks CodSpeed usam Python 3.13, workload fixo, 20 warmups e 100 rounds medidos.
`benchmarks/database.py` separa resultados PyMongo e Mongoz com 1.000 documentos, cinco warmups e nove
repetições. Estes resultados servem para regressões e releases, não para alegações de marketing.
