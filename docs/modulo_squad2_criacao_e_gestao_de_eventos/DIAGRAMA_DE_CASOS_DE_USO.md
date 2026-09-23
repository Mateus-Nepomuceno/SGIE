# Diagrama de Casos de Uso

## Atores

* **Usuário Autorizado:** Ator principal responsável por gerenciar o ciclo de vida do evento.

* **Sistema:** Ator responsável por ações automatizadas (ex: encerramento de inscrições).

## Casos de Uso e Relacionamentos

### 1. Criar Evento

O processo inicial de criação de um evento no sistema.

* **`<<include>>`** Informar dados do evento

  * **`<<include>>`** Informar dados obrigatórios

  * **`<<include>>`** Informar dados opcionais

### 2. Configurar Evento

Etapa de definição de regras e especificações do evento criado.

* **`<<include>>`** Configurar dados do evento

  * **`<<include>>`** Definir categoria e modalidade

    * **`<<extend>>`** Modalidade (Opções: *Online*, *Híbrido*, *Presencial*)

  * **`<<include>>`** Submissão

  * **`<<include>>`** Definir período e horários

  * **`<<extend>>`** Definir preço do evento (gratuito ou pago)

  * **`<<extend>>`** Definir local

    * **`<<include>>`** Auditório, sala, Laboratório ou outro

  * **`<<extend>>`** Capacidade

    * **`<<include>>`** Até 10.000 inscritos

  * **`<<extend>>`** Visibilidade

    * **`<<extend>>`** Público

    * **`<<extend>>`** Privado

  * **`<<extend>>`** Ajustar Equipe Organizadora

    * **`<<include>>`** Nome e e-mail públicos

### 3. Publicar Evento

Ação direta do usuário autorizado para tornar o evento publicado e visível.

### 4. Abrir Inscrições

Ação para permitir que os participantes se inscrevam no evento.

* **`<<include>>`** Gerenciar período de inscrições

* *(Ação do Sistema)* **`<<include>>`** Encerramento das inscrições

### 5. Alterar Evento

Ação de modificar detalhes de um evento existente.

* **`<<include>>`** Alterar dados do evento

### 6. Encerrar Evento

Ação de finalizar o ciclo de vida de um evento.

* **`<<include>>`** Cancelar evento

* **`<<include>>`** Marcar evento como Finalizado

*Legenda:*

* **`<<include>>`**: Relacionamento de inclusão (ação obrigatória ou parte dependente do caso de uso base).

* **`<<extend>>`**: Relacionamento de extensão (ação opcional ou condicional a partir do caso de uso base).