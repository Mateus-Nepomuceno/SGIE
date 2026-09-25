# Requisitos Funcionais e Regras de Negócio

## \[RFS01\] Cadastro de Evento

**Atores:** Usuário autorizado

Esse requisito começa quando o ator deseja criar um novo evento no sistema. Para isso ele deverá preencher os campos obrigatórios presentes na tabela 1.

**Tabela 1 - Campos obrigatórios para cadastro de evento**

| Nome do campo | Descrição do campo | 
 | ----- | ----- | 
| \* Nome do evento | Nome ou título do evento. | 
| \* Data | Data de realização do evento. | 
| \* Horário de início | Horário previsto para o início do evento. | 
| \* Horário de fim | Horário previsto para o encerramento do evento. | 
| \* Local | Local de realização do evento. | 
| \* Descrição | Descrição do evento, sem limite de caracteres. | 
| \* Limite de participantes | Quantidade máxima de participantes permitida no evento. | 
| \* Status de visibilidade | Define se o evento será privado ou público. | 
| \* Organizadores | Identificação da equipe organizadora do evento. | 
| \* Contatos | Número de telefone celular e e-mail para contato. | 

*(*) campos de preenchimento obrigatório\*

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS02\] Cadastro de Dados Opcionais do Evento

**Atores:** Usuário autorizado

Esse requisito começa quando o ator deseja complementar o cadastro do evento com informações não obrigatórias. O sistema deverá permitir o preenchimento dos campos presentes na tabela 2.

**Tabela 2 - Campos opcionais para cadastro de evento**

| Nome do campo | Descrição do campo | 
 | ----- | ----- | 
| Programação | Campo opcional para informar a programação do evento. | 
| Links | Campo opcional para inserir links relacionados ao evento. | 
| Banners | Campo opcional para adicionar banners relacionados ao evento. | 

**Prioridade:**

* \[ \] Essencial

* \[ \] Média

* \[x\] Baixa

## \[RFS03\] Validação do Título do Evento

**Atores:** Usuário autorizado

Esse requisito começa quando o ator informa o título do evento. O sistema deverá validar o conteúdo conforme as regras presentes na tabela 3.

**Tabela 3 - Regras para o título do evento**

| Regra | Descrição | 
 | ----- | ----- | 
| Quantidade de caracteres | O título deverá possuir no máximo 100 caracteres. | 
| Formatação | A letra inicial de todas as palavras do título deverá ser maiúscula. | 

**Prioridade:**

* \[ \] Essencial

* \[x\] Média

* \[ \] Baixa

## \[RFS04\] Configuração de Data e Horários

**Atores:** Usuário autorizado

Esse requisito começa quando o ator informa a data e os horários de realização do evento. O sistema deverá aceitar os valores conforme as regras presentes na tabela 4.

**Tabela 4 - Regras para data e horários do evento**

| Campo | Descrição | 
 | ----- | ----- | 
| Data | Deverá aceitar apenas números na ordem $dd/mm/aa$. | 
| Horário de início | Deverá aceitar apenas números seguindo o horário militar. | 
| Horário de fim | Deverá aceitar apenas números seguindo o horário militar. | 

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS05\] Configuração de Local e Modalidade

**Atores:** Usuário autorizado

Esse requisito começa quando o ator define onde e de que forma o evento será realizado. O sistema deverá disponibilizar as opções presentes na tabela 5.

**Tabela 5 - Opções para local e modalidade do evento**

| Campo | Descrição | 
 | ----- | ----- | 
| Local | Deverá permitir a escolha entre categorias de locais definidos, como auditório, sala 1 e laboratório 2, ou a opção outro, permitindo digitar o local. | 
| Modalidade | Deverá permitir selecionar Presencial, On-line ou Híbrido. | 

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS06\] Definição da Capacidade do Evento

**Atores:** Usuário autorizado

Esse requisito começa quando o ator define o limite de participantes do evento. O sistema deverá validar a capacidade conforme as regras presentes na tabela 6.

**Tabela 6 - Regras para capacidade do evento**

| Regra | Descrição | 
 | ----- | ----- | 
| Tipo de valor | A capacidade deverá aceitar apenas números. | 
| Limite máximo | A capacidade do evento deverá ser de até 10.000 inscritos. | 

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS07\] Definição da Categoria do Evento

**Atores:** Usuário autorizado

Esse requisito começa quando o ator seleciona a categoria do evento. O sistema deverá disponibilizar as categorias presentes na tabela 7.

**Tabela 7 - Categorias disponíveis para o evento**

| Categoria | Descrição | 
 | ----- | ----- | 
| Categorias predefinidas | Congresso, Simpósio, Seminário, Feira, Conferência, Festival, Competição, Workshop, Oficina, Curso, Mini-curso, Palestra, Roda de Conversa, Treinamento e Lançamento de Produto. | 
| Outro | Deverá permitir que o ator escreva uma categoria diferente das opções predefinidas. | 

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS08\] Configuração do Preço do Evento

**Atores:** Usuário autorizado

Esse requisito começa quando o ator define a condição de preço do evento. O sistema deverá disponibilizar as opções presentes na tabela 8.

**Tabela 8 - Opções de preço do evento**

| Opção | Descrição | 
 | ----- | ----- | 
| Gratuito | Define que o evento não possui cobrança para inscrição. | 
| Pago | Define que o evento possui cobrança para inscrição. | 

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS09\] Configuração da Equipe Organizadora e Contatos

**Atores:** Usuário autorizado

Esse requisito começa quando o ator informa os responsáveis pela organização do evento e os dados de contato. O sistema deverá armazenar as informações presentes na tabela 9.

**Tabela 9 - Dados da equipe organizadora e contatos**

| Nome do campo | Descrição do campo | 
 | ----- | ----- | 
| \* Nome do organizador | Nome do integrante da equipe organizadora. | 
| \* E-mail do organizador | E-mail do integrante da equipe organizadora, que deverá ser público. | 
| \* Telefone celular para contato | Número de telefone celular utilizado para contato do evento. | 
| \* E-mail para contato | E-mail utilizado para contato do evento. | 

*(*) campos de preenchimento obrigatório\*

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS10\] Definição da Visibilidade do Evento

**Atores:** Usuário autorizado

Esse requisito começa quando o ator define a visibilidade do evento. O sistema deverá permitir a seleção de uma das opções presentes na tabela 10.

**Tabela 10 - Opções de visibilidade do evento**

| Opção | Descrição | 
 | ----- | ----- | 
| Privado | Define o evento com status de visibilidade privada. | 
| Público | Define o evento com status de visibilidade pública. | 

**Prioridade:**

* \[ \] Essencial

* \[x\] Média

* \[ \] Baixa

## \[RFS11\] Publicação e Ciclo de Vida do Evento

**Atores:** Usuário autorizado

Esse requisito começa quando o ator gerencia o andamento do evento no sistema. O evento deverá seguir os estados do ciclo de vida presentes na tabela 11, incluindo o estado de publicação.

**Tabela 11 - Estados do ciclo de vida do evento**

| Estado | Descrição | 
 | ----- | ----- | 
| Rascunho | Estado inicial para elaboração do evento. | 
| Configuração | Estado em que os dados do evento estão sendo configurados. | 
| Publicado | Estado em que o evento foi publicado. | 
| Inscrições abertas | Estado em que o evento está recebendo inscrições. | 
| Em realização | Estado correspondente ao período de realização do evento. | 
| Finalizado | Estado utilizado após o término do evento. | 
| Arquivado | Estado utilizado para arquivamento do evento. | 

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS12\] Encerramento Automático das Inscrições

**Atores:** Sistema

Esse requisito começa quando o horário de início do evento se aproxima. O sistema deverá encerrar as inscrições automaticamente conforme a regra presente na tabela 12.

**Tabela 12 - Regra para encerramento das inscrições**

| Regra | Descrição | 
 | ----- | ----- | 
| Encerramento das inscrições | As inscrições realizadas pelo sistema deverão ser encerradas 15 minutos antes do começo do evento. | 

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS13\] Alteração de Evento

**Atores:** Usuário autorizado

Esse requisito começa quando o ator deseja alterar um evento já cadastrado. O sistema deverá permitir as alterações somente dentro dos prazos presentes na tabela 13.

**Tabela 13 - Prazos para alteração do evento**

| Dado | Regra para alteração | 
 | ----- | ----- | 
| Data do evento | Poderá ser alterada até 1 semana antes da data definida inicialmente. | 
| Horário | Poderá ser alterado até 1 hora antes do início do evento. | 
| Descrição | Poderá ser alterada até 1 hora antes do início do evento. | 
| Programação | Poderá ser alterada até 1 hora antes do início do evento. | 

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS14\] Cancelamento de Evento

**Atores:** Usuário autorizado

Esse requisito começa quando o ator deseja cancelar um evento. O sistema deverá validar o prazo permitido de acordo com a categoria do evento, conforme a tabela 14.

**Tabela 14 - Prazos para cancelamento do evento**

| Situação | Regra para cancelamento | 
 | ----- | ----- | 
| Regra geral | O cancelamento poderá ser realizado até 1 semana antes da data definida inicialmente. | 
| Eventos de curta duração | Oficina, Mini-curso, Palestra, Roda de Conversa, Treinamento, Lançamento de Produto e outros eventos de curta duração poderão ser cancelados com até 1 hora de antecedência. | 

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS15\] Configuração de Submissão de Trabalhos

**Atores:** Usuário autorizado

Esse requisito começa quando o ator define se o evento aceitará submissão de trabalhos. O sistema deverá permitir a configuração dessa funcionalidade conforme as opções presentes na tabela 15.

**Tabela 15 - Regra para submissão de trabalhos**

| Regra | Descrição | 
 | ----- | ----- | 
| Aceita submissão | Define que o evento permitirá a submissão de trabalhos pelos participantes. | 
| Não aceita submissão | Define que o evento não permitirá a submissão de trabalhos pelos participantes. | 

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa

## \[RFS16\] Definição do Período de Submissão de Trabalhos

**Atores:** Usuário autorizado

Esse requisito começa quando o ator deseja definir o período em que o evento aceitará submissões de trabalhos. O sistema deverá permitir a configuração da data e horário de início e fim das submissões, conforme as regras presentes na tabela 16.

**Tabela 16 - Configuração do período de submissão de trabalhos**

| Regra | Descrição | 
 | ----- | ----- | 
| Data e horário de início | Define a data e o horário a partir dos quais os participantes poderão realizar a submissão de trabalhos. | 
| Data e horário de fim | Define a data e o horário limite para que os participantes possam realizar a submissão de trabalhos. | 
| Validação do período | A data e o horário de fim deverão ser posteriores à data e ao horário de início do período de submissão. | 
| Encerramento das submissões | Após o término do período definido, o sistema não deverá permitir novas submissões de trabalhos. | 

**Prioridade:**

* \[x\] Essencial

* \[ \] Média

* \[ \] Baixa