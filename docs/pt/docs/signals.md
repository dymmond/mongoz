# Sinais

Por vezes, pode ser necessário *ouvir* um evento de documento ao salvar, ou seja, deseja-se realizar uma ação específica quando algo acontece nos modelos.

O Django, por exemplo, possui esse mecanismo chamado `Sinais`, que pode ser muito útil para esses casos e para realizar operações extras quando uma ação ocorre no documento.

Outros ORMs adotaram uma abordagem semelhante a essa e uma excelente foi o Ormar, que adotou a abordagem do Django na sua própria implementação.

O Mongoz, sendo como é desenhado, inspirou-se em ambas as abordagens e também suporta o `Sinal`.

## O que são Sinais

Sinais são mecanismos usados para acionar ações específicas quando ocorre um determinado tipo de evento nos modelos do Mongoz.

Da mesma forma que o Django aborda os sinais em termos de registro, o Mongoz faz isso de maneira semelhante.

## Sinais padrão

O Mongoz possui receptores padrão para cada documento criado no ecossistema. Eles podem ser usados prontamente a qualquer momento.

Também existem [sinais personalizados](#sinais-personalizados) caso queira algo "extra" além dos padrões fornecidos.

### Como usá-los

Os sinais estão dentro de `mongoz.core.signals` e para importá-los, basta executar:

``` python
from mongoz.core.signals import (
    post_delete,
    post_save,
    post_update,
    pre_delete,
    pre_save,
    pre_update,
)
```

#### pre_save

O `pre_save` é usado quando um documento está prestes a ser guardado e é acionado nas funções `Document.save()` e `Document.objects.create`.

```python
pre_save(send: Type["Document"], instance: "Document")
```

#### post_save

O `post_save` é usado após o documento já ter sido criado e guardado na base de dados, ou seja, quando uma instância já existe após o `save`. Esse sinal é acionado nas funções `Document.save()` e `Document.objects.create`.

```python
post_save(send: Type["Document"], instance: "Document")
```

#### pre_update

O `pre_update` é usado quando um documento está prestes a receber as atualizações e é acionado nas funções `Document.update()` e `Document.objects.update`.

```python
pre_update(send: Type["Document"], instance: "Document")
```

#### post_update

O `post_update` é usado quando um documento **já realizou as atualizações** e é acionado nas funções `Document.update()` e `Document.objects.update`.

```python
post_update(send: Type["Document"], instance: "Document")
```

#### pre_delete

O `pre_delete` é usado quando um documento está prestes a ser excluído e é acionado nas funções `Document.delete()` e `Document.objects.delete`.

```python
pre_delete(send: Type["Document"], instance: "Document")
```

#### post_delete

O `post_update` é usado quando um documento **já foi excluído** e é acionado nas funções `Document.delete()` e `Document.objects.delete`.

```python
post_update(send: Type["Document"], instance: "Document")
```

## Receptor

O receptor é a função ou ação que você deseja executar quando um sinal é acionado, noutras palavras, **é o que está a escutar um determinado evento**.

Vejamos um exemplo. Dado o seguinte documento.

```python
{!> ../../../docs_src/signals/receiver/document.py !}
```

Pode definir um *trigger* para enviar um e-mail ao utilizador registrado após a criação do registro usando o sinal `post_save`. A razão para usar o `post_save` é porque a notificação deve ser enviada **após** a criação do registro e não antes. Se fosse antes, o `pre_save` seria o sinal a ser usado.

```python hl_lines="11-12"
{!> ../../../docs_src/signals/receiver/post_save.py !}
```

Como pode ver, o decorador `post_save` está a apontar para o documento `User`, ou seja, está "a escutar" eventos nesse mesmo documento.

Isso é chamado de **receptor**.

Pode usar qualquer um dos [sinais padrão](#sinais-padrão) disponíveis ou até mesmo criar seu próprio [sinal personalizado](#sinais-personalizados).

### Requisitos

Ao definir a função ou `receptor`, ela deve atender aos seguintes requisitos:

* Deve ser um **callable**.
* Deve ter o argumento `sender` como primeiro parâmetro, que corresponde ao documento do objeto de envio.
* Deve ter o argumento `**kwargs` como parâmetro, pois cada documento pode mudar a qualquer momento.
* Deve ser `async` porque as operações de documento do Mongoz são aguardadas.

### Múltiplos receptores

E se você quiser usar o mesmo receptor para vários modelos? Vamos adicionar agora um documento adicional chamado `Profile`.

```python
{!> ../../../docs_src/signals/receiver/multiple.py !}
```

A maneira de definir o receptor para ambos pode ser facilmente alcançada da seguinte forma:

```python hl_lines="11"
{!> ../../../docs_src/signals/receiver/post_multiple.py !}
```

Desta forma, pode corresponder e executar qualquer lógica personalizada sem precisar se repetir muito e mantendo seu código limpo e consistente.

### Múltiplos receptores para o mesmo documento

E se agora quiser ter mais de um receptor para o mesmo documento? Na prática, colocaria todos num só lugar, mas talvez queira fazer algo completamente diferente e dividi-los em vários.

Pode facilmente fazer isso desta forma:

```python
{!> ../../../docs_src/signals/receiver/multiple_receivers.py !}
```

Isto garantirá que cada receptor execute a ação definida.

### Desconectando receptores

Se deseja desconectar o receptor e impedi-lo de ser executado para um determinado documento, também pode fazer isso de maneira simples.

```python hl_lines="20 23"
{!> ../../../docs_src/signals/receiver/disconnect.py !}
```

## Sinais Personalizados

Aqui é onde as coisas ficam interessantes. Muitas vezes, você querer ter o seu próprio `Sinal` e não depender apenas dos [padrões](#sinais-padrão) fornecidos, e isso é perfeitamente natural e comum.

O Mongoz permite que os sinais personalizados sejam usados de acordo com o seu próprio design.

Vamos continuar com o mesmo exemplo do documento `User`.

```python
{!> ../../../docs_src/signals/receiver/document.py !}
```

Agora deseja ter um sinal personalizado chamado `on_verify` especificamente adaptado às necessidades e lógica do seu `User`.

Para defini-lo, pode simplesmente fazer:

```python hl_lines="17"
{!> ../../../docs_src/signals/custom.py !}
```

Sim, é assim simples. Só precisa adicionar um novo sinal `on_verify` aos sinais do documento e, a partir de agora, o documento `User` terá um novo sinal pronto para ser usado.

!!! Warning
    Tenha em mente que **os sinais são do tipo nível de classe**, o que significa que afetarão todas as instâncias derivadas dele. Esteja atento ao criar um sinal personalizado e os seus impactos.

Agora deseja criar uma funcionalidade personalizada para ser ouvida no novo Sinal.

```python hl_lines="21 30"
{!> ../../../docs_src/signals/register.py !}
```

Agora, não apenas criou o novo receptor `trigger_notifications`, mas também o conectou ao novo sinal `on_verify`.

### Como usá-lo

Agora é hora de usar o sinal numa lógica personalizada, afinal, ele foi criado para garantir que seja personalizado o suficiente para as necessidades da lógica de negócio.

Para simplificação, o exemplo abaixo será uma lógica muito simples.

```python hl_lines="17"
{!> ../../../docs_src/signals/logic.py !}
```

Como pode ver, o `on_verify` é acionado apenas se o utilizador estiver verificado e não em nenhum outro lugar.

### Desconectar o sinal

O processo de desconectar o sinal é exatamente o [mesmo que antes](#desconectando-receptores).

```python hl_lines="10"
{!> ../../../docs_src/signals/disconnect.py !}
```
