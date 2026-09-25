# Diagrama de Classes

## Classes e Atributos

### Usuario_representante

* `id`

* `nome`

* `email`

### Evento

* `id`

* `nome`

* `descricao`

* `data`

* `horaInicio`

* `horaFim`

* `local`

* `modalidade`

* `capacidade`

* `status`

* `categoria`

* `e_gratuito`

### Regra_Submissao

* `id`

* `id_evento`

* `aceita_submissao`

* `data_hora_inicio`

* `data_hora_fim`

### Trabalho

* `id`

* `id_evento`

* `titulo`

* `arquivo_url`

* `nome_autor`

* `email_autor`

* `status`

### Link

* `id`

* `url`

* `descricao_link`

### Equipe_Organizadora

* `id`

* `nome`

* `email_publico`

### Contato

* `id`

* `telefone`

* `email`

### Banner

* `id`

* `arquivo_url`

### Programacao

* `id`

* `descricao`

* `horario`

## Relacionamentos e Cardinalidades

* **Usuario_representante** `organiza` **Evento**

  * `Usuario_representante` (1) ➔ (0..\*) `Evento`

* **Evento** `possui` **Regra_Submissao**

  * `Evento` (1) ➔ (0..1) `Regra_Submissao`

* **Evento** `possui` **Trabalho**

  * `Evento` (1) ➔ (0..\*) `Trabalho`

* **Evento** `possui` **Link**

  * `Evento` (1) ➔ (0..\*) `Link`

* **Evento** `possui` **Equipe_Organizadora**

  * `Evento` (1) ➔ (1..\*) `Equipe_Organizadora`

* **Evento** `possui` **Contato**

  * `Evento` (1) ➔ (1..\*) `Contato`

* **Evento** `possui` **Banner**

  * `Evento` (1) ➔ (0..\*) `Banner`

* **Evento** `possui` **Programacao**

  * `Evento` (1) ➔ (0..\*) `Programacao`