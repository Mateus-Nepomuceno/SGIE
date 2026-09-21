# Especificação de Requisitos Funcionais e Regras de Negócio

| Metadado | Detalhe |
|---|---|
| **Projeto** | SGIE — Sistema de Gestão de Inscrições e Eventos Universitários |
| **Módulo** | Usuários, Autenticação e Permissões (Squad 1) |
| **Responsável pelo Levantamento** | Gabriele Natividade |
| **Líder da Squad** | Luciano de Souza |
| **Data de Criação** | 21 de setembro de 2026 |
| **Versão** | 1.0.0 |
| **Status** | Homologado para Implementação |

---

## 1. Introdução e Visão Geral

Este documento formaliza os **Requisitos Funcionais (RF)** e as **Regras de Negócio (RN)** que regem o **Módulo de Usuários, Autenticação e Permissões** do SGIE.

O módulo atua como alicerce fundamental para todos os demais módulos do ecossistema (Gestão de Eventos, Inscrições, Submissões e Financeiro), sendo o responsável exclusivo por:
- Gerenciamento do ciclo de vida da conta dos usuários (cadastro, atualização e recuperação de acesso).
- Autenticação centralizada e emissão de sessões de usuário seguras.
- Atribuição, validação e hierarquia de papéis e permissões globais e contextuais por evento.
- Disponibilização padronizada dos dados cadastrais básicos para os módulos consumidores.

---

## 2. Requisitos Funcionais (RF)

### RF01 – Cadastrar Usuário
- **Descrição**: O sistema deve permitir que novos usuários se cadastrem na plataforma preenchendo um formulário padrão com seus dados de identificação pessoal e credenciais de segurança.
- **Campos Obrigatórios**:
  - `Nome Completo`: Texto (mínimo de 3 caracteres, obrigatório nome e sobrenome).
  - `E-mail`: Endereço de correio eletrônico válido e normalizado.
  - `CPF`: Cadastro de Pessoa Física com 11 dígitos, submetido a validação de dígito verificador.
  - `Data de Nascimento`: Data no formato `AAAA-MM-DD`, com validação de idade mínima.
  - `Número de Telefone`: Telefone/celular com DDD no padrão nacional `(XX) XXXXX-XXXX`.
  - `Senha`: Senha alfanumérica segura com hash criptográfico (PBKDF2/Argon2).
  - `Confirmação de Senha`: Campo idêntico à senha digitada.
- **Objetivo**: Registrar o usuário na plataforma base para que possa autenticar-se e interagir em eventos.
- **Fluxo Principal**:
  1. O usuário acessa a tela de cadastro (`/usuarios/cadastro/`).
  2. O usuário preenche todos os campos obrigatórios e submete o formulário.
  3. O sistema valida os formatos, checa a integridade dos dígitos do CPF e verifica se CPF ou E-mail já constam na base de dados.
  4. O sistema cria o registro com status ativo, armazena a senha criptografada e redireciona para a tela de login com mensagem de sucesso.
- **Critérios de Aceitação**:
  - Rejeitar cadastros com CPFs matematicamente inválidos.
  - Rejeitar cadastros caso CPF ou E-mail já existam no banco de dados (conforme `RN01`).
  - Senha deve ter no mínimo 8 caracteres e validação padrão Django.

---

### RF02 – Autenticar Usuário (Login)
- **Descrição**: O sistema deve permitir que o usuário previamente cadastrado efetue login para ter acesso autenticado às suas áreas restritas e funcionalidades do sistema.
- **Mecanismos de Autenticação**:
  1. **Autenticação Tradicional**:
     - O usuário pode informar seu **E-mail** OU seu **CPF** no mesmo campo de identificador, acompanhado de sua **Senha**.
  2. **Autenticação Integrada (Google OAuth2)**:
     - Login com um clique utilizando conta institucional ou pessoal Google, associando automaticamente o e-mail retornado ao usuário do sistema.
- **Objetivo**: Validar a identidade do usuário e iniciar uma sessão HTTP segura e rastreável.
- **Critérios de Aceitação**:
  - Suportar login indistintamente por CPF ou E-mail.
  - Exibir mensagem de erro genérica em caso de falha de credenciais ("Identificador ou senha inválidos"), prevenindo enumeração de contas.
  - Manter sessão ativa via cookies com flags `HttpOnly`, `SameSite=Lax` e `Secure` (em produção).

---

### RF03 – Recuperar Acesso
- **Descrição**: O sistema deve oferecer mecanismo seguro de recuperação de credenciais de acesso caso o usuário esqueça sua senha.
- **Mecanismos**:
  - O usuário informa seu e-mail cadastrado na tela de recuperação (`/usuarios/recuperar-senha/`).
  - O sistema gera um código numérico de verificação temporário (6 dígitos) com validade pré-fixada (ex.: 15 minutos) e o envia para o e-mail do usuário.
  - O usuário insere o código de verificação recebido e sua nova senha.
  - Após a validação do código, a nova senha é gravada e o código é invalidado imediatamente.
- **Critérios de Aceitação**:
  - Não informar na interface se o e-mail digitado existe ou não na base de dados (resposta uniforme).
  - Códigos expirados ou já utilizados devem ser sumariamente rejeitados.
  - O código deve expirar após o tempo limite ou após 3 tentativas incorretas consecutivas.

---

### RF04 – Atualizar Perfil de Organizador
- **Descrição**: O sistema deve permitir que um usuário com pretensão ou atribuição de papel de Organizador/Administrador personalize seu perfil público com dados adicionais.
- **Dados Adicionais**:
  - `Foto de Perfil`: Imagem do organizador (formatos JPG/PNG/WebP, tamanho máximo configurado).
  - `Banner Visual`: Imagem panorâmica de cabeçalho para eventos promovidos.
  - `Mini-biografia (Bio)`: Texto de apresentação pessoal/institucional (até 1.000 caracteres).
- **Objetivo**: Fornecer credibilidade, visibilidade institucional e identidade visual aos criadores e gestores de eventos universitários.
- **Critérios de Aceitação**:
  - Upload restrito a extensões de imagem permitidas e validação de MIME type.
  - Usuários que completam este formulário ganham a qualificação necessária para requerer ou receber status de Organizador de eventos.

---

### RF05 – Criar e Gerenciar Eventos (Controle de Acesso)
- **Descrição**: O sistema deve restringir a criação e gestão de eventos universitários exclusivamente a usuários qualificados como Organizadores ou Administradores do sistema.
- **Dados Base do Evento**: Nome do evento, Data de início, Data de fim e Local.
- **Critérios de Aceitação**:
  - Bloquear tentativas de criação de eventos por usuários que possuam apenas o papel básico de Participante.
  - Fornecer decorators/mixins de controle de permissão para serem utilizados nas rotas de criação do Módulo de Eventos (Squad 2).

---

### RF06 – Realizar Inscrição em Eventos (Seleção de Papéis)
- **Descrição**: O sistema deve permitir que um participante autenticado solicite sua inscrição em um determinado evento, indicando a função ou papel que deseja exercer.
- **Papéis Selecionáveis**:
  - `Participante / Ouvinte`: Acesso geral às atividades do evento.
  - `Voluntário`: Apoio operacional às atividades do evento.
  - `Suporte`: Atuação em logística, credenciamento e infraestrutura.
  - `Autor / Palestrante`: Usuário que submeterá trabalhos científicos ou conduzirá palestras/workshops.
  - `Avaliador`: Integrante da banca de revisão de submissões.
- **Critérios de Aceitação**:
  - Assegurar que os papéis solicitados sejam registrados no escopo específico do evento selecionado.
  - Integrar com o Módulo de Inscrições (Squad 3) através de IDs de usuário válidos.

---

### RF07 – Submeter Trabalhos e Documentos (Autores)
- **Descrição**: O sistema deve verificar e garantir que apenas usuários inscritos e homologados com o papel de **Autor/Palestrante** em determinado evento possam submeter documentos (artigos, resumos, apresentações, oficinas ou pesquisas).
- **Critérios de Aceitação**:
  - Fornecer método de consulta booleano (ex.: `has_event_permission(usuario, evento_id, 'AUTOR')`) para ser consumido pelo Módulo de Submissão.

---

### RF08 – Avaliar Trabalhos Submetidos (Avaliadores)
- **Descrição**: O sistema deve fornecer controle de permissão para que apenas membros designados da banca avaliativa (**Avaliadores**) visualizem, analisem e emitam notas/pareceres sobre as submissões enviadas pelos Autores.
- **Critérios de Aceitação**:
  - Fornecer método de consulta booleano (ex.: `has_event_permission(usuario, evento_id, 'AVALIADOR')`) para uso no Módulo de Avaliação.

---

## 3. Regras de Negócio (RN)

### RN01 – Unicidade de Cadastro
- **Descrição**: Cada CPF e cada endereço de E-mail inseridos no cadastro de usuário devem ser estritamente únicos na base de dados do SGIE.
- **Aplicação**: Não é permitido, sob qualquer hipótese, múltiplos cadastros com o mesmo CPF ou E-mail. Caso o usuário tente cadastrar um dado já existente, o sistema deve abortar a operação e exibir mensagem amigável de duplicidade.

---

### RN02 – Herança de Papéis Especiais (Especialização de Participante)
- **Descrição**: Todo Autor e todo Avaliador é obrigatoriamente um Participante registrado e ativo no sistema.
- **Aplicação**: Nenhum usuário pode atuar como Autor ou Avaliador de forma anônima ou desconectada. Apenas usuários autenticados previamente como Participantes podem se candidatar ou ser designados como autores ou membros de bancas examinadoras.

---

### RN03 – Multiplicidade de Papéis por Evento (Isolamento Contextual)
- **Descrição**: Um mesmo usuário cadastrado no sistema pode desempenhar diferentes papéis em eventos distintos de forma simultânea e independente.
- **Cenário Exemplo**:
  - O usuário `Carlos` pode ser **Organizador** no *Congresso de Computação (Evento A)*;
  - O mesmo `Carlos` pode ser **Autor / Palestrante** no *Simpósio de IA (Evento B)*;
  - E pode ser mero **Participante / Ouvinte** no *Seminário de Ética (Evento C)*.
- **Aplicação**: As permissões e autorizações devem ser avaliadas e tratadas estritamente de forma contextual, associando a tupla `(Usuário, Evento, Papel)`.

---

### RN04 – Promoção a Organizador / Administração
- **Descrição**: Para que um usuário com cadastro comum atue como Organizador ou Administrador de eventos, é obrigatório o preenchimento de um formulário estendido com informações adicionais.
- **Aplicação**: O preenchimento do formulário estendido (foto de perfil, banner visual e mini-biografia) habilita o usuário a criar e gerir eventos, conferindo credibilidade institucional e transparência pública aos organizadores.

---

### RN05 – Restrição de Submissão e Avaliação por Papel
- **Descrição**: O acesso às ações de submissão e de avaliação é restrito aos respectivos papéis homologados.
- **Aplicação**:
  - Apenas usuários homologados no papel de **Autor** no evento correspondente podem submeter trabalhos e apresentações.
  - Apenas usuários formalmente atribuídos à banca avaliativa (**Avaliadores**) têm acesso à visualização das submissões distribuídas e à emissão de notas/pareceres.

---

### RN06 – Disponibilidade de Dados de Usuário (Contrato de Compartilhamento)
- **Descrição**: As informações básicas de cadastro do usuário devem ser compartilhadas e disponibilizadas para os demais módulos e contextos de participação do sistema.
- **Aplicação**: Os campos `nome_completo`, `email`, `cpf`, `data_nascimento` e `telefone` devem ser expostos através de serviços internos e propriedades públicas da entidade `Usuario` para que módulos de Inscrição, Certificação, Submissão e Financeiro acessem tais dados sem duplicar tabelas de pessoas.

---

## 4. Matriz de Rastreabilidade (Requisitos x Regras de Negócio)

| Requisito Funcional | Regras de Negócio Aplicáveis | Impacto na Implementação |
|:---:|:---:|---|
| **RF01 – Cadastrar Usuário** | `RN01`, `RN06` | Constraints `unique=True` em CPF e e-mail; sanitização e formatação de campos; exposição para outros módulos. |
| **RF02 – Autenticar Usuário** | `RN01` | Backend customizado no Django para autenticar por CPF ou E-mail; suporte a OAuth2 Google. |
| **RF03 – Recuperar Acesso** | `RN01` | Código de uso único vinculado ao e-mail único do usuário com tempo de expiração. |
| **RF04 – Atualizar Perfil de Organizador** | `RN04` | Model `PerfilOrganizador` com campos de mídia (banner, foto) e biografia descritiva. |
| **RF05 – Criar e Gerenciar Eventos** | `RN03`, `RN04` | Validação se o criador possui `PerfilOrganizador` ativo e permissão global/local. |
| **RF06 – Inscrição em Eventos** | `RN02`, `RN03`, `RN06` | Tabela intermediária de papéis contextuais; garantia de que o usuário é previamente um Participante. |
| **RF07 – Submeter Trabalhos** | `RN02`, `RN03`, `RN05` | Guard de verificação de papel `AUTOR` associado ao evento específico. |
| **RF08 – Avaliar Trabalhos** | `RN02`, `RN03`, `RN05` | Guard de verificação de papel `AVALIADOR` associado à banca do evento. |
