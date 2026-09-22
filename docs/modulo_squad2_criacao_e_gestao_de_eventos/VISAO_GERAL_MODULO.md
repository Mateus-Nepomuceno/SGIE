# Criação e Gestão de Eventos

> **Objetivo:** Modelar como um usuário autorizado cria, configura, publica, altera e encerra um evento.

---

## Tarefas

### 1. Definição de Dados do Evento
- **Dados Obrigatórios:** Nome do evento, data, horário de início e fim, local, descrição, limite de participantes, status (privado ou público), organizadores, contatos (número de telefone celular e e-mail), submissões e modalidade de acesso.
- **Dados Opcionais:** Programação, links e banners.

### 2. Modelagem e Validação de Campos
- **Título:** Até 100 caracteres, com inicial maiúscula em todas as palavras.
- **Descrição:** Sem limite de caracteres.
- **Data:** Apenas números na ordem `dd/mm/aa`.
- **Hora:** Apenas números seguindo o horário militar (ex: 14:00).
- **Local:** Categorias definidas (auditório, sala 1, laboratório 2, etc.) ou *Outro* (campo de texto livre para digitar o local).
- **Modalidade:** Presencial, On-line ou Híbrido.
- **Capacidade:** Apenas números, com limite máximo de até 10.000 inscritos.

### 3. Categorias Disponíveis
- Congresso, Simpósio, Seminário, Feira, Conferência, Festival, Competição, Workshop, Oficina, Curso, Mini-curso, Palestra, Roda de Conversa, Treinamento, Lançamento de Produto ou *Outro* (campo de texto livre para escrever a categoria).

### 4. Configurações Adicionais
- **Período de inscrições:** As inscrições pelo sistema são encerradas automaticamente **15 minutos antes** do começo do evento.
- **Preço:** O evento pode ser definido como gratuito ou pago.
- **Submissão de trabalhos:** O organizador pode definir se o evento aceita ou não submissões de trabalhos.

### 5. Equipe Organizadora
- A equipe organizadora deverá ter nome e e-mail público para os participantes.

### 6. Ciclo de Vida do Evento
Os eventos devem transitar entre os seguintes status:
1. Rascunho
2. Configuração
3. Publicado
4. Inscrições abertas
5. Em realização
6. Finalizado
7. Arquivado

### 7. Regras para Alteração e Cancelamento (Eventos Publicados)
- **Alteração:** 
  - A *data* do evento pode ser mudada até **1 semana antes** da data definida inicialmente. 
  - *Horário*, *descrição* e *programação* podem ser modificados até **1 hora antes** do início do evento.
- **Cancelamento:** 
  - Regra geral: Pode ser feito até **1 semana antes** da data inicial. 
  - Exceção (Eventos de curta duração): Modalidades como Oficina, Mini-curso, Palestra, Roda de Conversa, Treinamento, Lançamento de Produto (e outros similares) podem ser cancelados com até **1 hora de antecedência**.

---

## Integração

### Contexto do Módulo
- **O que nosso módulo oferece?** Um app de gerenciamento de eventos.
- **De quais módulos dependemos?** Usuário, Autenticação e Permissões.
- **Quais dados precisamos receber?** Usuário autenticado.
- **Quais dados fornecemos?** Nome do evento, data, horário de início e fim, local, descrição, limite de participantes, status (privado ou público), organizadores, contatos (número de telefone celular e e-mail), submissões, modalidade de acesso, programação, links e banners.

### Regras de Negócio Exclusivas do Módulo

- **Cadastro do evento:** O evento deve ser criado por um usuário autorizado e conter obrigatoriamente nome, data, horário de início e fim, local, descrição, limite de participantes, visibilidade, organizadores e contatos. Programação, links e banners são opcionais.
- **Validação dos dados do evento:** O título deve ter no máximo 100 caracteres e todas as palavras devem iniciar com letra maiúscula. A descrição não possui limite de caracteres. A data deve seguir o formato `dd/mm/aa` e os horários devem seguir o horário militar.
- **Local e modalidade:** O local deve ser escolhido entre opções previamente definidas, com possibilidade de selecionar “Outro” e informar manualmente. A modalidade do evento deve ser Presencial, On-line ou Híbrido.
- **Capacidade do evento:** A capacidade deve aceitar somente valores numéricos e não pode ultrapassar 10.000 inscritos.
- **Categoria do evento:** O evento deve pertencer a uma das categorias predefinidas (Congresso, Simpósio, Seminário, Feira, Conferência, Festival, Competição, Workshop, Oficina, Curso, Mini-curso, Palestra, Roda de Conversa, Treinamento ou Lançamento de Produto) ou utilizar a opção “Outro”, permitindo informar uma categoria diferente.
- **Preço do evento:** O evento deve ser configurado como gratuito (sem cobrança de inscrição) ou pago (com cobrança).
- **Equipe organizadora e contatos:** Cada integrante da equipe organizadora deve possuir nome e e-mail público. O evento também deve possuir telefone celular e e-mail para contato geral.
- **Visibilidade do evento:** O evento deve ser definido como público ou privado.
- **Ciclo de vida do evento:** O evento deve seguir estritamente os estados: Rascunho, Configuração, Publicado, Inscrições abertas, Em realização, Finalizado e Arquivado.
- **Período de inscrições:** As inscrições devem ser encerradas automaticamente pelo sistema 15 minutos antes do início do evento.
- **Alteração do evento:** A data pode ser alterada até uma semana antes da data originalmente definida. Horário, descrição e programação podem ser modificados até uma hora antes do início do evento.
- **Cancelamento do evento:** Em regra, o cancelamento pode ser realizado até uma semana antes da data definida inicialmente. Eventos de curta duração (Oficina, Mini-curso, Palestra, Roda de Conversa, Treinamento e Lançamento de Produto) podem ser cancelados com até uma hora de antecedência.
- **Submissão de trabalhos:** O organizador deve definir se o evento aceita ou não submissão de trabalhos. Quando aceita, os participantes poderão realizar submissões; quando não aceita, essa funcionalidade não deverá estar disponível ou visível.
- **Período de submissão de trabalhos:** Nos eventos que aceitam submissões, deve ser definido um período com data e horário de início e fim. O término deve ser posterior ao início e, após o encerramento do período, o sistema não deverá aceitar novas submissões.