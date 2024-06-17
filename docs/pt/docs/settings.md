# Definições

Quem nunca teve aquela sensação de que às vezes seria bom ter algumas configurações de base de dados? Bem, como o Mongoz é do mesmo autor do [Esmerald][esmerald] e como o [Esmerald][esmerald] é orientado a [configurações][esmerald_settings], por que não aplicar o mesmo princípio, mas de maneira mais simples, ao Mongoz?

Foi exatamente isso que aconteceu.

## Módulo de Configurações do Mongoz

A forma de usar o objeto de configurações no ORM do Mongoz é através de:

* **MONGOZ_SETTINGS_MODULE** variável de ambiente.

Todas as configurações são objetos **[Pydantic BaseSettings](https://pypi.org/project/pydantic-settings/)**, o que torna mais fácil de usar e substituir quando necessário.

### MONGOZ_SETTINGS_MODULE

Por padrão, o Mongoz procura por uma variável de ambiente `MONGOZ_SETTINGS_MODULE` para executar e aplicar as configurações fornecidas à sua instância.

Se nenhuma `MONGOZ_SETTINGS_MODULE` for encontrada, o Mongoz usa as suas próprias configurações internas, que são amplamente aplicadas em todo o sistema.

#### Configurações personalizadas

Ao criar sua própria classe de configurações personalizadas, deve herdar de `MongozSettings`, que é a classe responsável por todas as configurações internas do Mongoz e que podem ser estendidas e substituídas com facilidade.

Algo como isto:

```python title="myproject/configs/settings.py"
{!> ../../../docs_src/settings/custom_settings.py !}
```

Super simples, certo? Sim, e essa é a intenção. O Mongoz não tem muitas configurações, mas tem algumas que são usadas em todo o código e que podem ser facilmente substituídas.

!!! Danger
    Tenha cuidado ao substituir as configurações, pois pode quebrar a funcionalidade. É por sua conta e risco.

[esmerald_settings]: https://esmerald.dev/application/settings/
[esmerald]: https://esmerald.dev/
