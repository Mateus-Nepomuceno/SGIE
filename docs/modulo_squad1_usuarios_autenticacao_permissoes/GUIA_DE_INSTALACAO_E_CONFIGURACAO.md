# Guia de Instalação e Configuração do Módulo de Usuários

| Metadado | Detalhe |
|---|---|
| **Projeto** | SGIE — Sistema de Gestão de Inscrições e Eventos Universitários |
| **Módulo** | Usuários, Autenticação e Permissões (Squad 1) |
| **Público-Alvo** | Desenvolvedores das equipes de Squad 1, 2, 3, 4 e 5 |
| **Data de Criação** | 21 de setembro de 2026 |
| **Versão** | 1.0.0 |
| **Status** | Homologado para Uso |

---

## 1. Pré-Requisitos de Ambiente

Para executar e desenvolver o Módulo de Usuários do SGIE localmente, é necessário dispor de:
- **Python 3.12** ou superior (compatível com Python 3.13).
- **Git** configurado para versionamento.
- **Ambiente virtual** (`venv`).
- Terminal compatível com Bash ou PowerShell.

---

## 2. Passo a Passo de Instalação e Execução

### 2.1 Clonar o Repositório e Acessar o Diretório
```bash
git clone https://github.com/Mateus-Nepomuceno/apiSGIE.git
cd apiSGIE
```

### 2.2 Ativar o Ambiente Virtual
- **No Linux/macOS**:
  ```bash
  python -m venv venv
  source venv/bin/activate
  ```
- **No Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

### 2.3 Instalar as Dependências do Projeto
```bash
pip install --upgrade pip
# Para dependências de produção / base:
pip install -r requirements.txt

# Para ambiente de desenvolvimento completo (incluindo linter Ruff e testes):
pip install -r requirements-dev.txt
```


### 2.4 Configurar as Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo padrão de desenvolvimento:

```env
DJANGO_SECRET_KEY=sua-chave-secreta-de-desenvolvimento-sgie-2026
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

> **Nota**: Durante o desenvolvimento local, o envio de e-mails de recuperação de senha utiliza o backend de console (`django.core.mail.backends.console.EmailBackend`), imprimindo o código de 6 dígitos diretamente no terminal de execução do servidor.

### 2.5 Configurar os Hooks de Commit Padronizados
Para garantir a aderência às convenções de commit do projeto (`docs/COMMITS.md`):
```bash
bash scripts/commits/install.sh
```

### 2.6 Aplicar as Migrações do Banco de Dados
```bash
# Gerar arquivos de migração do app usuarios (se necessário)
python manage.py makemigrations usuarios

# Aplicar todas as migrações no banco SQLite local
python manage.py migrate
```

### 2.7 Criar um Superusuário (Administrador)
```bash
python manage.py createsuperuser
```
*Preencha o Nome Completo, E-mail, CPF, Data de Nascimento, Telefone e Senha quando solicitado.*

### 2.8 Executar a Suíte de Testes Automatizados
Certifique-se de que todos os testes unitários e de integração estão passando com sucesso:
```bash
python manage.py test usuarios
```

### 2.9 Iniciar o Servidor de Desenvolvimento
```bash
python manage.py runserver
```
O sistema estará acessível em:
- **Painel Administrativo**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **Cadastro de Usuários**: [http://127.0.0.1:8000/usuarios/cadastro/](http://127.0.0.1:8000/usuarios/cadastro/)
- **Login do Sistema**: [http://127.0.0.1:8000/usuarios/login/](http://127.0.0.1:8000/usuarios/login/)
- **Recuperação de Senha**: [http://127.0.0.1:8000/usuarios/recuperar-senha/](http://127.0.0.1:8000/usuarios/recuperar-senha/)
- **Perfil do Usuário**: [http://127.0.0.1:8000/usuarios/perfil/](http://127.0.0.1:8000/usuarios/perfil/)

---

## 3. Resolução de Problemas Comuns

1. **Erro de `AUTH_USER_MODEL` não reconhecido**:
   - Certifique-se de que `'usuarios'` está listado em `INSTALLED_APPS` no arquivo `core/settings.py` antes de rodar `migrate`.
2. **Erro de upload de imagens (Mídia)**:
   - O suporte a `ImageField` requer a biblioteca `Pillow`, que já está homologada e incluída no `requirements.txt`. Certifique-se de que as dependências do projeto foram instaladas via `pip install -r requirements.txt`.
3. **Código de verificação não chega por e-mail**:
   - Em ambiente local, observe o terminal onde o comando `python manage.py runserver` está em execução; a mensagem de e-mail é exibida diretamente no console.
