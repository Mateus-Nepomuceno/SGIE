# Diagrama de Casos de Uso: Sistema de Inscrição em Eventos

**Escopo:** Sistema de Inscrição em Eventos - Inscrições e Participantes

# Atores

* **Participante:** Usuário que realiza e gerencia sua própria inscrição no evento.

* **Organizador:** Usuário responsável pela validação e controle dos participantes do evento.

# Casos de Uso por Ator

### Participante

O ator **Participante** se relaciona diretamente com os seguintes casos de uso:

* **Realizar Inscrição**

  * Inclui (`<<Include>>`) o caso de uso *Verificar Disponibilidade de Vagas*.

  * Inclui (`<<Include>>`) o caso de uso *Atualizar Situação da Inscrição*.

* **Entrar na Lista de Espera**

  * Estende (`<<Extend>>`) o caso de uso *Realizar Inscrição* sob a condição `[sem vaga]`.

* **Consultar Inscrições**

* **Desistir da Lista de Espera**

* **Cancelar Inscrição**

  * Inclui (`<<Include>>`) o caso de uso *Atualizar Situação da Inscrição*.

### Organizador

O ator **Organizador** se relaciona diretamente com os seguintes casos de uso:

* **Validar Comprovante de Categoria**

  * Inclui (`<<Include>>`) o caso de uso *Atualizar Situação da Inscrição*.

* **Consultar Participantes**

* **Registrar Presença**

## Casos de Uso Internos (Compartilhados / Sistema)

Esses casos de uso não possuem ligação direta com os atores, mas são acionados a partir de outros casos de uso através de relacionamentos de inclusão ou extensão:

* **Verificar Disponibilidade de Vagas:** Acionado sempre que uma inscrição é realizada.

* **Atualizar Situação da Inscrição:** Funciona como um ponto centralizado de atualização de status, sendo incluído por *Realizar Inscrição*, *Validar Comprovante de Categoria* e *Cancelar Inscrição*, e servindo como base de extensão para *Emitir Ingresso*.

* **Emitir Ingresso**

  * Estende (`<<Extend>>`) o caso de uso *Atualizar Situação da Inscrição* sob a condição `[inscrição confirmada]`.

## Código Mermaid

```mermaid
flowchart LR
    P["Participante"]
    O["Organizador"]

    subgraph Sistema ["Sistema de Inscrição em Eventos - Inscrições e Participantes"]
        direction TB
        UC1(["Verificar Disponibilidade de Vagas"])
        UC2(["Realizar Inscrição"])
        UC3(["Entrar na Lista de Espera"])
        UC4(["Consultar Inscrições"])
        UC5(["Desistir da Lista de Espera"])
        UC6(["Atualizar Situação da Inscrição"])
        UC7(["Emitir Ingresso"])
        UC8(["Cancelar Inscrição"])

        UC9(["Validar Comprovante de Categoria"])
        UC10(["Consultar Participantes"])
        UC11(["Registrar Presença"])
    end

    P --- UC2
    P --- UC3
    P --- UC4
    P --- UC5
    P --- UC8

    O --- UC9
    O --- UC10
    O --- UC11

    UC2 -. "<< Include >>" .-> UC1
    UC2 -. "<< Include >>" .-> UC6
    UC3 -. "<< Extend >><br>[sem vaga]" .-> UC2

    UC9 -. "<< Include >>" .-> UC6
    UC8 -. "<< Include >>" .-> UC6

    UC7 -. "<< Extend >><br>[inscrição confirmada]" .-> UC6

    classDef actor fill:transparent,stroke:none,font-weight:bold,color:#333;
    class P,O actor;
```
