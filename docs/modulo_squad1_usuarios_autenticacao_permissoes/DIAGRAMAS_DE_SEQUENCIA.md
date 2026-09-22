# Diagramas de Sequência — Fluxos de Interação

| Metadado | Detalhe |
|---|---|
| **Projeto** | SGIE — Sistema de Gestão de Inscrições e Eventos Universitários |
| **Módulo** | Usuários, Autenticação e Permissões (Squad 1) |
| **Responsável pela Modelagem** | Luciano de Souza |
| **Líder da Squad** | Luciano de Souza |
| **Data de Criação** | 21 de setembro de 2026 |
| **Versão** | 1.0.0 |
| **Status** | Homologado para Implementação |

---

## 1. Introdução

Este documento formaliza a ordem cronológica e a troca de mensagens entre os componentes do sistema (Usuário, Navegador, Controladores Django, Camada de Negócio e Banco de Dados).

Os diagramas expandem a modelagem inicial registrada em `diagrama_sequencia_cadastro_login.pdf` para cobrir os fluxos completos de Cadastro, Login Tradicional, Autenticação Google, Recuperação de Acesso e Atualização de Perfil.

---

## 2. Diagrama 1: Cadastro de Usuário (RF01)

Representa o preenchimento do formulário padrão, validação de unicidade de CPF/E-mail (`RN01`) e persistência segura no banco de dados.

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário
    participant B as Navegador / Frontend
    participant V as View (CadastroView)
    participant F as Form (CadastroUsuarioForm)
    participant S as UsuarioService
    participant DB as Banco de Dados

    U->>B: Acessa rota /usuarios/cadastro/
    B->>V: GET /usuarios/cadastro/
    V-->>B: Renderiza cadastro.html com token CSRF

    U->>B: Preenche dados (Nome, Email, CPF, Data Nasc, Tel, Senha)
    U->>B: Clica em "Cadastrar"
    B->>V: POST /usuarios/cadastro/ com dados do formulário
    V->>F: Instancia Form com request.POST
    F->>F: Executa validações (CPF matemático, formato de telefone)
    F->>DB: Consulta existência de CPF ou E-mail (RN01)
    DB-->>F: Registros não encontrados (OK)
    
    V->>S: Invoca criar_novo_usuario(dados_validados)
    S->>S: Aplica hash na senha (PBKDF2)
    S->>DB: INSERT INTO usuarios_usuario(...)
    DB-->>S: Confirma inserção com novo ID
    S-->>V: Retorna instância do Usuário criado
    
    V-->>B: Redireciona 302 para /usuarios/login/ (com mensagem flash de sucesso)
    B-->>U: Exibe tela de login com alerta "Cadastro realizado com sucesso!"
```

---

## 3. Diagrama 2: Autenticação Tradicional — Login por E-mail ou CPF (RF02)

Demonstra a resolução de login híbrido suportando tanto e-mail quanto CPF no mesmo campo de entrada.

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário
    participant B as Navegador / Frontend
    participant V as View (LoginView)
    participant A as Django Authentication Backend
    participant DB as Banco de Dados
    participant S as Gerenciador de Sessão

    U->>B: Acessa /usuarios/login/
    B->>V: GET /usuarios/login/
    V-->>B: Renderiza login.html

    U->>B: Informa identificador (E-mail ou CPF) e Senha
    U->>B: Clica em "Entrar"
    B->>V: POST /usuarios/login/
    V->>A: authenticate(request, username=identificador, password=senha)
    
    A->>DB: Busca usuário WHERE email = identificador OR cpf = identificador
    alt Usuário Encontrado e Ativo
        DB-->>A: Retorna registro do usuário
        A->>A: Compara hash da senha (check_password)
        alt Senha Válida
            A-->>V: Retorna objeto Usuario
            V->>S: django.contrib.auth.login(request, user)
            S-->>B: Grava cookie sessionid (HttpOnly, Secure)
            V-->>B: Redireciona para /painel/
            B-->>U: Exibe Painel do Usuário logado
        else Senha Inválida
            A-->>V: Retorna None
            V-->>B: Renderiza login.html com erro "Credenciais inválidas"
        end
    else Usuário Não Encontrado ou Inativo
        DB-->>A: Nenhum registro retornado
        A-->>V: Retorna None
        V-->>B: Renderiza login.html com erro "Credenciais inválidas"
    end
```

---

## 4. Diagrama 3: Fluxo de Recuperação de Acesso por Código (RF03)

Ilustra o envio do código de 6 dígitos via e-mail e a redefinição subsequente de credenciais.

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário
    participant B as Navegador / Frontend
    participant V as View (RecuperarSenhaView)
    participant S as UsuarioService
    participant M as Servidor de E-mail (SMTP/Console)
    participant DB as Banco de Dados

    %% Etapa 1: Solicitação
    U->>B: Acessa /usuarios/recuperar-senha/ e informa seu E-mail
    B->>V: POST /usuarios/recuperar-senha/ (acao="solicitar_codigo")
    V->>S: gerar_codigo_recuperacao(email)
    S->>DB: Localiza usuário por e-mail
    opt Usuário Existe
        S->>S: Gera código de 6 dígitos (ex: 739104) com validade de 15 min
        S->>DB: INSERT INTO usuarios_codigorecuperacao(...)
        S->>M: Despacha e-mail com código de verificação
    end
    S-->>V: Confirmação de disparo
    V-->>B: Redireciona para tela de inserção do código e nova senha

    %% Etapa 2: Redefinição
    U->>M: Abre e-mail e copia o código recebido
    U->>B: Insere Código, Nova Senha e Confirmação
    B->>V: POST /usuarios/redefinir-senha/ (codigo, nova_senha)
    V->>S: redefinir_senha_com_codigo(email, codigo, nova_senha)
    S->>DB: SELECT * FROM usuarios_codigorecuperacao WHERE codigo=codigo AND utilizado=FALSE
    
    alt Código Válido e Dentro do Prazo (< 15 min)
        DB-->>S: Código localizado com sucesso
        S->>S: Aplica hash na nova senha
        S->>DB: UPDATE usuarios_usuario SET password=hash WHERE id=user_id
        S->>DB: UPDATE usuarios_codigorecuperacao SET utilizado=TRUE WHERE id=codigo_id
        S-->>V: Sucesso na redefinição
        V-->>B: Redireciona para login com mensagem de sucesso
        B-->>U: "Senha atualizada com sucesso! Efetue login."
    else Código Inválido ou Expirado
        S-->>V: Lança exceção de código inválido
        V-->>B: Exibe mensagem de erro "Código inválido ou expirado"
    end
```

---

## 5. Diagrama 4: Atualização de Perfil de Organizador (RF04, RN04)

Evidencia a expansão de um participante comum para organizador institucional através de upload de mídia e mini-bio.

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário Autenticado
    participant B as Navegador / Frontend
    participant V as View (PerfilView)
    participant F as Form (PerfilOrganizadorForm)
    participant S as UsuarioService
    participant FS as Armazenamento de Arquivos (/media/)
    participant DB as Banco de Dados

    U->>B: Acessa /usuarios/perfil/organizador/
    B->>V: GET /usuarios/perfil/organizador/
    V-->>B: Renderiza formulário estendido com campos de foto, banner e bio

    U->>B: Anexa Foto, Banner e digita mini-biografia
    U->>B: Clica em "Salvar Perfil de Organizador"
    B->>V: POST multipart/form-data (arquivos e texto)
    V->>F: Valida tipos de arquivo (MIME image/*) e tamanho máximo
    
    V->>S: atualizar_perfil_organizador(usuario, dados, arquivos)
    S->>FS: Salva arquivos sanitizados em /media/organizadores/
    FS-->>S: Retorna caminhos relativos das imagens salvas
    S->>DB: INSERT/UPDATE usuarios_perfilorganizador(...)
    DB-->>S: Confirmação de persistência
    S-->>V: Retorna perfil atualizado
    
    V-->>B: Redireciona para /usuarios/perfil/ com status atualizado
    B-->>U: Exibe "Perfil de Organizador atualizado e pronto para criar eventos!"
```
