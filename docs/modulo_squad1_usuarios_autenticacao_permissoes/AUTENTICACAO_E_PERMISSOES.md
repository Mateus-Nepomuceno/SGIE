# Especificação de Autenticação e Matriz de Permissões (RBAC)

| Metadado | Detalhe |
|---|---|
| **Projeto** | SGIE — Sistema de Gestão de Inscrições e Eventos Universitários |
| **Módulo** | Usuários, Autenticação e Permissões (Squad 1) |
| **Modelo de Segurança** | RBAC Contextual (Role-Based Access Control por Evento) |
| **Data de Criação** | 21 de setembro de 2026 |
| **Versão** | 1.0.0 |
| **Status** | Homologado para Implementação |

---

## 1. Visão Geral

O SGIE adota uma estratégia de controle de acesso híbrida, combinando **permissões globais de sistema** com **permissões contextuais por evento** (RBAC Contextual).

Essa estrutura assegura que um mesmo usuário possa exercer múltiplas funções em diferentes eventos de forma simultânea e isolada (`RN03`), além de impor as regras estritas de herança (`RN02`) e restrição de acesso a submissões e avaliações (`RN05`).

---

## 2. Mecanismos de Autenticação

### 2.1 Backend Híbrido: `EmailOrCPFBackend`
Para proporcionar máxima usabilidade, o SGIE não força o usuário a memorizar um *username* arbitrário. O login pode ser realizado informando **E-mail** OU **CPF** em um único campo.

- **Fluxo de Autenticação**:
  1. O backend recebe o identificador e a senha fornecidos.
  2. Remove pontuações e traços caso o formato se assemelhe a um CPF (`\D`).
  3. Realiza consulta ORM com `Q(email__iexact=identificador) | Q(cpf=cpf_limpo)`.
  4. Se o usuário for encontrado e estiver ativo (`is_active=True`), valida a senha através de `user.check_password(password)`.
  5. Retorna a instância autenticada ou `None`.

### 2.2 Autenticação Integrada: Google OAuth2
- Permite que discentes e docentes realizem login rápido com sua conta Google (`RF02`).
- Caso o e-mail retornado pelo Google já esteja cadastrado no sistema, a sessão é vinculada à conta existente.
- Caso o e-mail não exista, o usuário é direcionado a um formulário complementar simplificado para preenchimento de CPF e Telefone (dados obrigatórios do SGIE conforme `RF01`).

### 2.3 Recuperação de Acesso por Código Seguro (`RF03`)
- Códigos gerados com gerador pseudoaleatório criptograficamente seguro (`secrets` do Python).
- O código possui 6 dígitos numéricos (ex.: `581903`).
- Validade estrita de 15 minutos (`expira_em = timezone.now() + timedelta(minutes=15)`).
- Bloqueio após 3 tentativas incorretas para prevenir ataques de força bruta.
- Invalidação automática após a primeira utilização bem-sucedida.

---

## 3. Matriz de Papéis e Permissões

### 3.1 Níveis de Papéis no Sistema

| Papel | Escopo | Descrição e Capacidades |
|---|:---:|---|
| **Visitante (Anônimo)** | Global | Pode visualizar página pública de eventos, cadastrar-se e solicitar recuperação de senha. |
| **Participante** | Global / Evento | Usuário autenticado básico. Pode inscrever-se em eventos e gerenciar seu perfil. |
| **Organizador / ADM** | Global / Evento | Usuário qualificado com perfil estendido. Pode criar eventos, gerir inscrições e comissões. |
| **Autor** | Contextual por Evento | Participante homologado para submeter trabalhos e apresentações em um evento específico (`RN05`). |
| **Avaliador** | Contextual por Evento | Participante designado para a banca avaliativa de um evento específico (`RN05`). |
| **Palestrante / Voluntário** | Contextual por Evento | Papéis operacionais associados à programação ou logística do evento. |
| **Superadministrador** | Global | Acesso irrestrito via Django Admin para auditoria técnica e governança do sistema. |

---

### 3.2 Matriz de Acesso por Operação

| Funcionalidade / Operação | Visitante | Participante | Organizador | Autor (no evento) | Avaliador (no evento) |
|---|:---:|:---:|:---:|:---:|:---:|
| Visualizar Lista Pública de Eventos | ✔ | ✔ | ✔ | ✔ | ✔ |
| Cadastrar-se na Plataforma | ✔ | — | — | — | — |
| Efetuar Login e Logout | ✔ | ✔ | ✔ | ✔ | ✔ |
| Recuperar Senha por E-mail | ✔ | ✔ | ✔ | ✔ | ✔ |
| Visualizar e Editar Perfil Pessoal | — | ✔ | ✔ | ✔ | ✔ |
| Preencher Perfil Estendido de Organizador | — | ✔ | ✔ | ✔ | ✔ |
| Criar Novo Evento | — | — | ✔ | — | — |
| Inscrever-se em Evento (como Ouvinte) | — | ✔ | ✔ | ✔ | ✔ |
| Candidatar-se a Voluntário / Suporte | — | ✔ | ✔ | ✔ | ✔ |
| Submeter Artigo / Documento no Evento | — | — | — | ✔ (`RN05`) | — |
| Avaliar Trabalhos Submetidos no Evento | — | — | — | — | ✔ (`RN05`) |
| Emitir Certificados de Participação | — | — | ✔ | — | — |

---

## 4. Regras de Segurança e Decorators

### 4.1 Decorator de Autenticação (`@login_required`)
Redireciona usuários anônimos para `/usuarios/login/?next=/url/alvo/`.

### 4.2 Decorator de Organizador (`@organizador_required`)
Verifica se o usuário possui registro ativo em `PerfilOrganizador` com `homologado=True` ou se é superusuário. Caso contrário, redireciona para a tela de solicitação de perfil com mensagem explicativa.

### 4.3 Decorator de Papel Contextual (`@role_required(papel, evento_param='evento_id')`)
Implementado em `usuarios/permissions.py`:
```python
def role_required(papel_esperado, evento_param='evento_id'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('usuarios:login')
            evento_id = kwargs.get(evento_param)
            if not UsuarioService.verificar_papel_evento(request.user, evento_id, papel_esperado):
                raise PermissionDenied('Acesso restrito ao papel especificado neste evento.')
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
```
Esse decorator é exportado pelo Módulo de Usuários para que os Módulos de Submissão e Avaliação protejam suas respectivas rotas.
