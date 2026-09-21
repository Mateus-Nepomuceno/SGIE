# Convenção e Validação de Mensagens de Commit

Este projeto adota uma política padronizada para mensagens de commit baseada no [Conventional Commits v1.0.0](https://www.conventionalcommits.org/pt-br/v1.0.0/) e adaptada da referência comunitária [iuricode/padroes-de-commits](https://github.com/iuricode/padroes-de-commits).

A validação é executada automaticamente pelo hook local `commit-msg` do Git antes que qualquer commit seja registrado no histórico.

---

## 1. Estrutura da Mensagem de Commit

Toda mensagem de commit deve seguir a estrutura:

```text
<tipo>[(escopo)][!]: <descrição>

[corpo opcional explicando os motivos e o contexto da alteração]

[rodapés opcionais, ex.: BREAKING CHANGE: ..., Refs: #123]
```

### Regras do Cabeçalho:
1. **`<tipo>`**: Obrigatório e em minúsculas. Indica a intenção principal da alteração.
2. **`[(escopo)]`**: Opcional. Delimitado por parênteses contendo apenas `[a-zA-Z0-9_.-]+` (ex.: `(auth)`, `(core)`). Não utilize parênteses vazios `()`.
3. **`[!]:`**: Opcional. Indica *Breaking Change* (mudança incompatível) na API ou comportamento.
4. **`: `**: Separador obrigatório composto de dois-pontos e exatamente **um** espaço ASCII.
5. **`<descrição>`**: Resumo sucinto da alteração. Deve iniciar sem espaços extras e não ter espaços em branco no final. Permite português, caracteres Unicode e emojis descritivos.

---

## 2. Tipos Permitidos e Semântica

| Tipo | Descrição Semântica | SemVer Associado | Emojis Recomendados na Descrição |
| :--- | :--- | :---: | :--- |
| `feat` | Inclusão de um novo recurso ou funcionalidade | MINOR | ✨ `:sparkles:`, 💄 `:lipstick:` |
| `fix` | Correção de um defeito ou bug | PATCH | 🐛 `:bug:`, 💥 `:boom:` |
| `docs` | Modificações exclusivas em documentação | PATCH | 📚 `:books:`, 💡 `:bulb:` |
| `test` | Criação, refatoração ou exclusão de testes | PATCH | ✅ `:white_check_mark:`, 🧪 `:test_tube:` |
| `build` | Modificações no sistema de build ou dependências | PATCH | ➕ `:heavy_plus_sign:`, 📦 `:package:` |
| `perf` | Melhorias no tempo de resposta ou desempenho | PATCH | ⚡ `:zap:` |
| `style` | Formatação de código sem alteração lógica | PATCH | 🎨 `:art:`, 👌 `:ok_hand:` |
| `refactor` | Refatoração de código sem alterar comportamento | PATCH | ♻️ `:recycle:` |
| `chore` | Manutenção de tarefas rotineiras, ferramentas | PATCH | 🔧 `:wrench:`, 🚚 `:truck:` |
| `ci` | Alterações em arquivos de CI (workflows, scripts) | PATCH | 🧱 `:bricks:` |
| `raw` | Alterações em dados brutos, fixtures e configurações | PATCH | 🗃️ `:card_file_box:` |
| `cleanup` | Limpeza de código comentado ou arquivos mortos | PATCH | 🧹 `:broom:` |
| `remove` | Remoção definitiva de recursos ou módulos | PATCH / MAJOR | 🗑️ `:wastebasket:` |
| `revert` | Reversão de commits anteriores do histórico | Variável | ⏪ `:rewind:` |

> **Atenção:** O tipo `init` **não** é permitido pela gramática padrão. O commit inicial do repositório deve usar:
> ```bash
> git commit -m "chore: iniciar projeto"
> ```

---

## 3. Exemplos

### Válidos
- `feat(auth): adicionar autenticação via JWT`
- `fix(api)!: alterar resposta do endpoint de usuários`
- `feat: ✨ permitir download de relatórios em CSV`
- `docs: 📚 atualizar documentação da API no README`
- `raw: atualizar fixtures de cidades e estados`
- `cleanup: remover código comentado no módulo de login`
- `remove: excluir rotas legadas v1`
- `revert: desfazer alteração ineficiente na consulta SQL`

### Inválidos e Motivos
- `:sparkles: feat: adicionar login` -> *Emoji antes do tipo (rejeitado por parsers padrão).*
- `[feat] ✨: adicionar login` -> *Tipo entre colchetes.*
- `Feat: adicionar login` -> *Tipo com letra maiúscula.*
- `feature: adicionar login` -> *Tipo 'feature' não existe na lista (use 'feat').*
- `feat(): adicionar login` -> *Escopo vazio entre parênteses.*
- `feat(auth):` -> *Descrição ausente.*
- `feat:  adicionar login` -> *Dois espaços após os dois-pontos.*
- `chore: ajustar rotina ` -> *Espaço em branco no final da linha.*

---

## 4. Instalação e Gerenciamento dos Hooks

### Ativação no Repositório Local
Para ativar o hook localmente, execute o instalador:
```bash
bash scripts/commits/install.sh
```
O instalador configura `git config --local core.hooksPath .githooks` e salva um manifesto com checksums em `.git/commit-hooks-manifest.json`. Reexecuções são *no-op*.

### Desinstalação e Rollback
Para desativar o hook e restaurar a configuração anterior:
```bash
bash scripts/commits/uninstall.sh
```

### Execução dos Testes
Para rodar a suíte completa de testes automatizados (unitários e de integração):
```bash
bash scripts/commits/test.sh
```
