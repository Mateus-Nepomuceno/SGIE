# Mostra de Código e Legenda — Módulo de Usuários, Autenticação e Permissões

| Metadado | Detalhe |
|---|---|
| **Projeto** | SGIE — Sistema de Gestão de Inscrições e Eventos Universitários |
| **Módulo** | Usuários, Autenticação e Permissões (Squad 1) |
| **Artefato** | 14 — Mostra de Código e Legenda Arquitetural |
| **Data de Conclusão** | 21 de setembro de 2026 |
| **Versão** | 1.0.0 |
| **Status** | Concluído e Validado (28/28 Testes Aprovados) |

---

## 1. Visão Geral da Entrega

Este documento consolida a entrega final do **Módulo de Usuários, Autenticação e Permissões**, fornecendo a legenda de todos os componentes, classes, métodos públicos, formulários, rotas e tabelas implementadas em conformidade com os Requisitos Funcionais (`RF01` a `RF08`) e Regras de Negócio (`RN01` a `RN06`).

---

## 2. Estrutura de Arquivos Entregue

```text
SGIE/
├── core/
│   ├── settings.py           # Configurações globais (AUTH_USER_MODEL, backends, etc.)
│   ├── urls.py               # Roteador central (/usuarios/ e /api/sgie/v1/)
│   └── api_router.py         # Roteador REST v1 para consumo inter-squads
│
└── usuarios/
    ├── migrations/
    │   └── 0001_initial.py   # Migração inicial do esquema de dados
    ├── templates/usuarios/
    │   ├── cadastro.html     # HTML funcional semântico de registro (RF01)
    │   ├── login.html        # HTML funcional semântico de login híbrido (RF02)
    │   ├── recuperar_senha.html # HTML funcional de recuperação em 2 etapas (RF03)
    │   └── perfil.html       # HTML funcional de perfil e organizador (RF04, RN04, RN06)
    ├── __init__.py
    ├── admin.py              # Customização do Django Admin
    ├── apps.py               # Configuração do aplicativo Django
    ├── backends.py           # EmailOrCPFBackend para autenticação híbrida
    ├── forms.py              # Formulários de validação e sanitização de dados
    ├── models.py             # Modelos ORM (Usuario, PerfilOrganizador, CodigoRecuperacao, PapelContextual)
    ├── permissions.py        # Decorators (@organizador_required, @role_required) e DRF Permissions
    ├── serializers.py        # Serializers DRF para integração
    ├── services.py           # Camada de serviços públicos (UsuarioService)
    ├── tests.py              # Suíte de 28 testes automatizados
    ├── urls.py               # Roteamento web e endpoints de API do app
    └── validators.py         # Validações matemáticas de CPF, telefone e imagem
```

---

## 3. Legenda das Entidades de Dados (`models.py`)

| Classe / Modelo | Herança / Base | Descrição e Atribuição |
|---|---|---|
| `UsuarioManager` | `BaseUserManager` | Gerenciador customizado com `create_user` e `create_superuser`. Normaliza e-mails e higieniza CPFs. |
| `Usuario` | `AbstractBaseUser`, `PermissionsMixin` | Entidade central de identidade do SGIE (`AUTH_USER_MODEL`). Suporta CPF único, e-mail único, métodos `has_role`, `is_organizador` e propriedade `cpf_formatado`. |
| `PerfilOrganizador` | `models.Model` | Extensão 1-para-1 do usuário contendo foto de perfil, banner institucional e mini-biografia para qualificação de organizadores (`RN04`). |
| `CodigoRecuperacao` | `models.Model` | Código de verificação numérico de 6 dígitos com expiração estrita de 15 minutos e consumo único (`RF03`). |
| `Papel` | `models.TextChoices` | Enumeração de papéis: `PARTICIPANTE`, `AUTOR`, `AVALIADOR`, `ORGANIZADOR`, `PALESTRANTE`, `VOLUNTARIO`, `SUPORTE`. |
| `PapelContextual` | `models.Model` | Associação de multiplicidade contextual entre Usuário e Evento com unicidade composta `(usuario, evento_id, papel)` (`RN03`). |

---

## 4. Legenda dos Serviços Públicos (`services.py`)

A classe `UsuarioService` expõe os métodos de integração para consumo interno e por outros módulos:

| Método | Assinatura | Função |
|---|---|---|
| `cadastrar_usuario` | `(nome_completo, email, cpf, data_nascimento, telefone, password, **extra)` | Criação atômica de conta com senha sob hash criptográfico (`RF01`). |
| `autenticar_usuario` | `(request, identificador, senha)` | Autenticação híbrida transparente por CPF ou E-mail (`RF02`). |
| `gerar_codigo_recuperacao` | `(email)` | Gera código aleatório via `secrets`, salva expiração e despacha e-mail (`RF03`). Resposta uniforme para proteção contra enumeração. |
| `redefinir_senha_com_codigo` | `(email, codigo, nova_senha)` | Valida token temporal e uso único, altera senha e consome código (`RF03`). |
| `atualizar_perfil_organizador` | `(usuario, foto, banner, bio, homologado)` | Persiste mídias e dados descritivos para promoção a organizador (`RF04`, `RN04`). |
| `obter_dados_cadastrais` | `(usuario_id)` | Contrato público com dados civis para certificados, eventos e financeiro (`RN06`). |
| `verificar_papel_evento` | `(usuario_ou_id, evento_id, papel_esperado)` | Consulta se usuário possui autorização contextual no evento (`RN03`, `RN05`). |
| `atribuir_papel_evento` | `(usuario_ou_id, evento_id, papel, ativo)` | Atribui ou atualiza papel contextual no evento (`RN02`, `RN03`). |
| `is_organizador_homologado` | `(usuario_ou_id)` | Avalia elegibilidade para criação de eventos (`RN04`). |

---

## 5. Legenda de Permissões e Segurança (`permissions.py`)

| Decorator / Classe | Finalidade |
|---|---|
| `@organizador_required` | Intercepta requisições HTTP e exige perfil de organizador homologado ou superusuário para avançar. |
| `@role_required(papel, evento_param)` | Valida dinamicamente se o usuário logado possui o papel requerido no evento indicado nos parâmetros da rota. |
| `IsOrganizadorPermission` | Classe de permissão do DRF para endpoints restritos a organizadores. |
| `HasEventRolePermission` | Classe de permissão do DRF para endpoints restritos por papel contextual no evento. |

---

## 6. Rotas e Endpoints Registrados

| Rota HTTP | Método(s) | Descrição |
|---|---|---|
| `/usuarios/cadastro/` | GET, POST | Tela e processamento de cadastro de novos usuários. |
| `/usuarios/login/` | GET, POST | Autenticação híbrida por E-mail ou CPF. |
| `/usuarios/logout/` | GET, POST | Encerramento seguro de sessão. |
| `/usuarios/recuperar-senha/` | GET, POST | Etapa 1: solicitação de código de recuperação por e-mail. |
| `/usuarios/redefinir-senha/` | GET, POST | Etapa 2: validação do código de 6 dígitos e definição de nova senha. |
| `/usuarios/perfil/` | GET, POST | Painel de perfil pessoal e submissão de perfil de organizador. |
| `/usuarios/login/google/` | GET | Ponto de entrada para fluxo integrado Google OAuth2. |
| `/api/sgie/v1/usuarios/` | GET, POST | API REST para CRUD de usuários. |
| `/api/sgie/v1/organizadores/` | GET, POST | API REST para perfis de organizadores. |
| `/api/sgie/v1/papeis-contextuais/` | GET, POST | API REST para verificação e concessão de papéis em eventos. |
| `/api/sgie/v1/usuarios/dados-cadastrais/` | GET | API REST do contrato de dados cadastrais (`RN06`). |

---

## 7. Resultados dos Testes Automatizados e Linters

- **Django Test Runner**: 28 testes executados com 100% de sucesso (`OK`).
- **Ruff Linter**: 0 erros (`All checks passed!`).
- **Ruff Formatter**: 100% dos arquivos formatados (`22 files already formatted`).
