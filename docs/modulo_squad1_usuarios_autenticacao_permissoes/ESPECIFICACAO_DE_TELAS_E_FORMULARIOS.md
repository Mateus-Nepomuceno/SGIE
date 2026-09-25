# Especificação de Telas e Formulários (Fase 1)

| Metadado | Detalhe |
|---|---|
| **Projeto** | SGIE — Sistema de Gestão de Inscrições e Eventos Universitários |
| **Módulo** | Usuários, Autenticação e Permissões (Squad 1) |
| **Estágio** | Fase 1 — HTML Funcional Puro (Sem Estilização CSS) |
| **Data de Criação** | 21 de setembro de 2026 |
| **Versão** | 1.0.0 |
| **Status** | Homologado para Implementação |

---

## 1. Diretriz da Fase 1 (HTML Funcional)

Conforme estabelecido no item 2.6 da **Ata de Reunião** (`docs/docs_base/ATA_REUNIAO.md`):

> *"Desenvolver a view funcional da sua parte — HTML com textos, campos de formulário, botões e links entre páginas funcionando corretamente e integrados ao back-end, sem estilização CSS (sem cores, sem formatação visual), priorizando a estrutura e o funcionamento."*

A equipe de Design/Front-end aplicará a estilização unificada e os tokens de design posteriormente na Fase 2. Portanto, os templates deste módulo devem focar exclusivamente em semântica HTML5, segurança CSRF, acessibilidade (`labels` vinculados) e exibição clara de mensagens de feedback do Django (`django.contrib.messages`).

---

## 2. Especificação Detalhada das Telas

### 2.1 Tela 1: Cadastro de Usuário (`cadastro.html`)
- **Arquivo**: `usuarios/templates/usuarios/cadastro.html`
- **Rota**: `/usuarios/cadastro/` (Nome: `usuarios:cadastro`)
- **Métodos**: `GET` (renderização) e `POST` (processamento)
- **Requisitos Cobertos**: `RF01`, `RN01`, `RN06`

#### Elementos da Interface:
1. **Título da Página**: `<h1>Cadastro de Usuário - SGIE</h1>`
2. **Área de Mensagens**: Bloco condicional para renderização de erros do formulário e alertas flash.
3. **Formulário** (`<form method="post">`):
   - `{% csrf_token %}` (Obrigatório)
   - Campo Nome Completo: `<input type="text" name="nome_completo" required maxlength="150">`
   - Campo E-mail: `<input type="email" name="email" required>`
   - Campo CPF: `<input type="text" name="cpf" required placeholder="000.000.000-00" maxlength="14">`
   - Campo Data de Nascimento: `<input type="date" name="data_nascimento" required>`
   - Campo Telefone: `<input type="tel" name="telefone" required placeholder="(71) 99999-9999">`
   - Campo Senha: `<input type="password" name="password1" required minlength="8">`
   - Campo Confirmação de Senha: `<input type="password" name="password2" required minlength="8">`
   - Botão de Submissão: `<button type="submit">Cadastrar</button>`
4. **Navegação**:
   - Link: `<a href="{% url 'usuarios:login' %}">Já possui uma conta? Faça login</a>`

---

### 2.2 Tela 2: Autenticação / Login (`login.html`)
- **Arquivo**: `usuarios/templates/usuarios/login.html`
- **Rota**: `/usuarios/login/` (Nome: `usuarios:login`)
- **Métodos**: `GET` e `POST`
- **Requisitos Cobertos**: `RF02`

#### Elementos da Interface:
1. **Título da Página**: `<h1>Entrar no SGIE</h1>`
2. **Formulário Tradicional** (`<form method="post">`):
   - `{% csrf_token %}`
   - Campo Identificador: `<input type="text" name="identificador" required placeholder="Digite seu E-mail ou CPF">`
   - Campo Senha: `<input type="password" name="password" required placeholder="Digite sua senha">`
   - Botão de Acesso: `<button type="submit">Entrar</button>`
3. **Autenticação Federada Google**:
   - Botão/Link dedicado: `<a href="{% url 'usuarios:google_login' %}">Entrar com Conta Google</a>`
4. **Links de Apoio**:
   - `<a href="{% url 'usuarios:recuperar_senha' %}">Esqueceu sua senha?</a>`
   - `<a href="{% url 'usuarios:cadastro' %}">Não tem uma conta? Cadastre-se</a>`

---

### 2.3 Tela 3: Recuperação de Acesso (`recuperar_senha.html`)
- **Arquivo**: `usuarios/templates/usuarios/recuperar_senha.html`
- **Rotas**:
  - `/usuarios/recuperar-senha/` (Etapa 1: Solicitar código)
  - `/usuarios/redefinir-senha/` (Etapa 2: Inserir código e redefinir)
- **Requisitos Cobertos**: `RF03`, `RN01`

#### Elementos da Interface:
1. **Etapa 1 — Solicitação de Código**:
   - Título: `<h1>Recuperar Senha</h1>`
   - Descrição: `<p>Informe o e-mail cadastrado para enviarmos o código de verificação.</p>`
   - Campo: `<input type="email" name="email" required>`
   - Botão: `<button type="submit">Enviar Código</button>`
2. **Etapa 2 — Validação e Nova Senha**:
   - Título: `<h1>Redefinir Senha com Código</h1>`
   - Descrição: `<p>Insira o código de 6 dígitos recebido por e-mail e sua nova senha.</p>`
   - Campo Código: `<input type="text" name="codigo" required maxlength="6" placeholder="123456">`
   - Campo Nova Senha: `<input type="password" name="nova_senha" required minlength="8">`
   - Campo Confirmação: `<input type="password" name="confirmacao_senha" required minlength="8">`
   - Botão: `<button type="submit">Salvar Nova Senha</button>`

---

### 2.4 Tela 4: Perfil do Usuário e Organizador (`perfil.html`)
- **Arquivo**: `usuarios/templates/usuarios/perfil.html`
- **Rota**: `/usuarios/perfil/` (Nome: `usuarios:perfil`)
- **Métodos**: `GET` e `POST`
- **Requisitos Cobertos**: `RF04`, `RN04`, `RN06`

#### Elementos da Interface:
1. **Título da Página**: `<h1>Meu Perfil</h1>`
2. **Dados Cadastrais Básicos (Leitura e Edição)**:
   - Exibição de Nome, E-mail, CPF, Data de Nascimento e Telefone.
   - Opção para atualizar Telefone ou Nome.
3. **Painel de Qualificação de Organizador (`RN04`)**:
   - Título: `<h2>Perfil de Organizador de Eventos</h2>`
   - Mensagem explicativa sobre a necessidade do perfil para criação e gestão de eventos.
   - Formulário com `enctype="multipart/form-data"`:
     - `{% csrf_token %}`
     - Foto de Perfil: `<input type="file" name="foto_de_perfil" accept="image/*">`
     - Banner Institucional: `<input type="file" name="banner" accept="image/*">`
     - Mini-biografia: `<textarea name="bio_do_organizador" rows="4" cols="50" maxlength="1000" placeholder="Escreva sobre sua experiência e atuação acadêmica..."></textarea>`
     - Botão: `<button type="submit" name="acao" value="salvar_organizador">Atualizar Perfil de Organizador</button>`
4. **Encerramento de Sessão**:
   - Formulário/Link de Logout: `<a href="{% url 'usuarios:logout' %}">Sair do Sistema (Logout)</a>`
