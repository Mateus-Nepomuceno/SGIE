# Plano de Testes e Validação da Qualidade

| Metadado | Detalhe |
|---|---|
| **Projeto** | SGIE — Sistema de Gestão de Inscrições e Eventos Universitários |
| **Módulo** | Usuários, Autenticação e Permissões (Squad 1) |
| **Framework de Testes** | Django Test Runner (`django.test.TestCase`) |
| **Data de Criação** | 21 de setembro de 2026 |
| **Versão** | 1.0.0 |
| **Status** | Homologado para Implementação |

---

## 1. Visão Geral e Estratégia de Testes

A suíte de testes do **Módulo de Usuários** visa garantir 100% de conformidade com os Requisitos Funcionais (`RF01`–`RF08`) e Regras de Negócio (`RN01`–`RN06`), prevenindo regressões e garantindo integração segura com os fluxos de CI/CD do repositório (`.github/workflows/django.yml`).

A estratégia organiza os testes em quatro camadas:
1. **Testes Unitários de Modelos**: Validação de integridade do banco e hashing de senhas.
2. **Testes Unitários de Formulários**: Sanitização de dados, validação de CPFs e senhas.
3. **Testes de Serviços de Negócio**: Lógica pura de autenticação, expiração de códigos e RBAC.
4. **Testes de Integração de Views e Rotas**: Fluxo HTTP, controle de sessões e redirecionamentos.

---

## 2. Matriz de Casos de Teste Planejados

### 2.1 Camada de Modelos (`usuarios/tests.py`)

| ID | Cenário de Teste | Entrada / Pré-condição | Resultado Esperado | Requisito / Regra |
|:---:|---|---|---|:---:|
| **CT-MOD-01** | Criar usuário com dados válidos | Nome, email, CPF válido, data nasc, tel, senha | Usuário salvo no banco com senha criptografada (`password != raw_password`) | `RF01` |
| **CT-MOD-02** | Bloquear duplicidade de e-mail | Dois cadastros com o mesmo e-mail | Lançamento de `IntegrityError` na gravação do segundo | `RN01` |
| **CT-MOD-03** | Bloquear duplicidade de CPF | Dois cadastros com o mesmo CPF | Lançamento de `IntegrityError` na gravação do segundo | `RN01` |
| **CT-MOD-04** | Criar superusuário | `create_superuser` com dados válidos | `is_staff=True`, `is_superuser=True`, `is_active=True` | Governança |
| **CT-MOD-05** | Expiração de código de recuperação | `CodigoRecuperacao` emitido há 16 minutos | `is_valido()` retorna `False` | `RF03` |
| **CT-MOD-06** | Consumo único de código | `CodigoRecuperacao` com flag `utilizado=True` | `is_valido()` retorna `False` | `RF03` |

---

### 2.2 Camada de Formulários (`usuarios/forms.py`)

| ID | Cenário de Teste | Entrada / Pré-condição | Resultado Esperado | Requisito / Regra |
|:---:|---|---|---|:---:|
| **CT-FRM-01** | Validar CPF com dígitos inválidos | CPF com 11 dígitos, mas cálculo do DV incorreto | Formulário inválido com mensagem de erro "CPF inválido" | `RF01` |
| **CT-FRM-02** | Rejeitar senhas divergentes | `password1="Senha123"` e `password2="Senha456"` | Formulário inválido com erro "As senhas não coincidem" | `RF01` |
| **CT-FRM-03** | Aceitar login com formato de E-mail | `identificador="user@teste.com"` | Formulário válido | `RF02` |
| **CT-FRM-04** | Aceitar login com formato de CPF | `identificador="12345678901"` ou `"123.456.789-01"` | Formulário válido | `RF02` |
| **CT-FRM-05** | Validar arquivos no Perfil de Organizador | Upload de arquivo `.exe` ou `.pdf` no banner | Formulário inválido; aceitar apenas extensões de imagem | `RF04`, `RN04` |

---

### 2.3 Camada de Serviços (`usuarios/services.py`)

| ID | Cenário de Teste | Entrada / Pré-condição | Resultado Esperado | Requisito / Regra |
|:---:|---|---|---|:---:|
| **CT-SRV-01** | Geração e despacho de código | E-mail de usuário cadastrado | Registro criado na tabela e e-mail adicionado ao *outbox* | `RF03` |
| **CT-SRV-02** | Solicitação para e-mail inexistente | E-mail que não consta no banco | Não lança erro nem cria código (resposta neutra para segurança) | `RF03` |
| **CT-SRV-03** | Redefinição bem-sucedida de senha | Código correto, dentro da validade, nova senha | Senha do usuário alterada e código marcado como utilizado | `RF03` |
| **CT-SRV-04** | Verificação de papel em evento | Usuário com papel `AUTOR` no evento 1 | `verificar_papel_evento(u, 1, 'AUTOR')` retorna `True` | `RN03`, `RN05` |
| **CT-SRV-05** | Isolamento de papel entre eventos | Usuário é `AUTOR` no evento 1, mas não no evento 2 | `verificar_papel_evento(u, 2, 'AUTOR')` retorna `False` | `RN03`, `RN05` |

---

### 2.4 Camada de Views e Rotas (`usuarios/views.py`)

| ID | Cenário de Teste | Rota / Método | Resultado Esperado | Requisito / Regra |
|:---:|---|---|---|:---:|
| **CT-VIW-01** | Acesso GET à tela de cadastro | `/usuarios/cadastro/` (GET) | Código HTTP 200 e template `cadastro.html` renderizado | `RF01` |
| **CT-VIW-02** | Submissão com sucesso no cadastro | `/usuarios/cadastro/` (POST válido) | Código HTTP 302 redirecionando para `/usuarios/login/` | `RF01` |
| **CT-VIW-03** | Login com credenciais válidas | `/usuarios/login/` (POST correto) | Redirecionamento 302 e cookie de sessão gravado | `RF02` |
| **CT-VIW-04** | Login com credenciais inválidas | `/usuarios/login/` (POST incorreto) | Código HTTP 200 mantendo na tela com mensagem flash de erro | `RF02` |
| **CT-VIW-05** | Acesso não autenticado a página protegida | `/usuarios/perfil/` (GET anônimo) | Redirecionamento 302 para `/usuarios/login/?next=/usuarios/perfil/` | Segurança |
| **CT-VIW-06** | Logout de usuário autenticado | `/usuarios/logout/` (POST ou GET) | Sessão destruída e redirecionamento para tela inicial/login | Segurança |

---

## 3. Instruções de Execução dos Testes

Para executar toda a suíte de testes do módulo de usuários localmente:

```bash
# Executar todos os testes do módulo usuários com verbosidade
python manage.py test usuarios -v 2

# Executar apenas testes de modelos
python manage.py test usuarios.tests.TestUsuarioModel

# Executar testes com relatório de cobertura (opcional)
coverage run --source='usuarios' manage.py test usuarios
coverage report -m
```
