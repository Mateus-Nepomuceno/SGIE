# Arquitetura Técnica do Módulo de Usuários

| Metadado | Detalhe |
|---|---|
| **Projeto** | SGIE — Sistema de Gestão de Inscrições e Eventos Universitários |
| **Módulo** | Usuários, Autenticação e Permissões (Squad 1) |
| **Padrão Arquitetural** | Django MTV (Model-Template-View) + Service Layer Desacoplada |
| **Data de Criação** | 21 de setembro de 2026 |
| **Versão** | 1.0.0 |
| **Status** | Homologado para Implementação |

---

## 1. Visão Geral da Arquitetura

O **Módulo de Usuários** foi arquitetado sobre o framework **Django 5+ / 6+**, adotando o padrão **Model-Template-View (MTV)** enriquecido com uma **Camada de Serviços (`services.py`)**.

Essa abordagem previne os antipadrões clássicos de *Fat Models* (modelos sobrecarregados com lógica de infraestrutura e disparo de e-mails) e *Fat Views* (controladores repletos de validações de regras de negócio), garantindo alta testabilidade, baixo acoplamento e conformidade com as diretrizes do molde estrutural (`molde_modulo_usuarios.zip`).

---

## 2. Topologia de Diretórios e Arquivos

```text
SGIE/
├── core/                                # Configurações Globais do Projeto
│   ├── settings.py                     # AUTH_USER_MODEL, Backends de autenticação e Mídia
│   ├── urls.py                         # Roteador central (aponta /usuarios/ para o app)
│   └── wsgi.py / asgi.py               # Pontos de entrada para servidores web
│
└── usuarios/                           # App do Módulo de Usuários
    ├── migrations/                     # Histórico versionado de migrações do banco
    │   └── __init__.py
    ├── templates/
    │   └── usuarios/                   # Namespace isolado de templates HTML puro
    │       ├── cadastro.html           # Tela de registro de usuário (RF01)
    │       ├── login.html              # Tela de autenticação e Google OAuth (RF02)
    │       ├── recuperar_senha.html    # Tela de recuperação por código (RF03)
    │       └── perfil.html             # Painel de perfil e organizador (RF04)
    ├── __init__.py
    ├── admin.py                        # Registro customizado no Django Admin
    ├── apps.py                         # Configuração e inicialização do app
    ├── forms.py                        # Formulários de validação e sanitização de dados
    ├── models.py                       # Entidades ORM (Usuario, PerfilOrganizador, etc.)
    ├── permissions.py                  # Decorators e classes de checagem de papéis
    ├── services.py                     # Camada de serviços e regras de negócio puras
    ├── tests.py                        # Suíte de testes automatizados (unitários e integração)
    ├── urls.py                         # Rotas desacopladas do módulo
    └── views.py                        # Controladores HTTP de orquestração
```

---

## 3. Responsabilidade de Cada Camada

### 3.1 Camada de Dados (`models.py`)
- Define as tabelas e relações no banco de dados.
- O modelo `Usuario` herda de `AbstractBaseUser` e `PermissionsMixin`, fornecendo suporte a hash de senhas, permissões globais e campos de auditoria (`date_joined`, `last_login`).
- Implementa o `UsuarioManager` para gerenciar a criação de contas normais e superusuários garantindo CPF e e-mail únicos.
- Contém apenas validações intrínsecas de consistência relacional e propriedades derivadas simples.

### 3.2 Camada de Validação de Entrada (`forms.py`)
- Responsável pela integridade, sanitização e validação dos dados submetidos pelo usuário antes de atingirem o banco.
- Formulários principais:
  - `CadastroUsuarioForm`: Valida dígitos verificadores do CPF, máscara de telefone e unicidade preliminar.
  - `AutenticacaoForm`: Sanitiza o campo de identificador (E-mail ou CPF) e senha.
  - `RecuperarSenhaForm` e `RedefinirSenhaForm`: Validam o formato do e-mail e a conformidade do código de 6 dígitos.
  - `PerfilOrganizadorForm`: Valida uploads de imagens (extensão, tamanho em bytes e dimensões mínimas).

### 3.3 Camada de Negócio (`services.py`)
- Isola toda a lógica de negócio do framework web, facilitando testes sem necessidade de simular requisições HTTP completas.
- Funções e serviços:
  - `UsuarioService.cadastrar_usuario(...)`: Criação de usuário com hash e defaults.
  - `UsuarioService.gerar_codigo_recuperacao(...)`: Geração segura de token numérico e despacho via e-mail.
  - `UsuarioService.validar_e_redefinir_senha(...)`: Conferência temporal e expiração de códigos.
  - `UsuarioService.atualizar_perfil_organizador(...)`: Processamento de upload de fotos e banners.
  - `UsuarioService.verificar_papel_evento(...)`: Verificação de autorização contextual por evento.

### 3.4 Camada de Controle e Apresentação (`views.py` e `templates/`)
- Orquestra a requisição HTTP: recebe os dados, aciona o formulário correspondente, invoca a camada de serviços e devolve a resposta adequada.
- Em conformidade com a Fase 1 da Ata de Reunião, os templates em `usuarios/templates/usuarios/` utilizam **HTML semântico puro**, priorizando inputs funcionais, mensagens de erro e feedback (`messages`), sem dependência de estilização externa ou frameworks CSS pesados.

### 3.5 Camada de Segurança e Autorização (`permissions.py`)
- Fornece decorators e mixins para proteger views contra acessos indevidos:
  - `@login_required`: Exige sessão autenticada.
  - `@role_required(papel, evento_param='evento_id')`: Verifica se o usuário autenticado possui o papel requerido no contexto do evento especificado na rota.

---

## 4. Integração com o Núcleo Global (`core/`)

O aplicativo é plugado no sistema global através de:
1. **Registro do Modelo em `core/settings.py`**:
   ```python
   AUTH_USER_MODEL = 'usuarios.Usuario'
   AUTHENTICATION_BACKENDS = [
       'usuarios.backends.EmailOrCPFBackend',
       'django.contrib.auth.backends.ModelBackend',
   ]
   ```
2. **Roteamento em `core/urls.py`**:
   ```python
   from django.urls import path, include

   urlpatterns = [
       path('admin/', admin.site.urls),
       path('usuarios/', include('usuarios.urls', namespace='usuarios')),
   ]
   ```
3. **Mídia de Uploads em `core/settings.py`**:
   ```python
   MEDIA_URL = '/media/'
   MEDIA_ROOT = BASE_DIR / 'media'
   ```
