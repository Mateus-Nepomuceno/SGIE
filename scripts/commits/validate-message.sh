#!/usr/bin/env bash
set -e

ALLOWED_TYPES="feat|fix|docs|test|build|perf|style|refactor|chore|ci|raw|cleanup|remove|revert"

STANDARD_REGEX="^(${ALLOWED_TYPES})(\([a-zA-Z0-9_.-]+\))?(!)?:\ ([^[:space:]]|[^[:space:]].*[^[:space:]])$"

LEGACY_PREFIX_REGEX="^(:[a-zA-Z0-9_+-]+:|[^[:alnum:][:space:]]+)[[:space:]]+"

if [ $# -lt 1 ]; then
  echo "ERRO: Caminho do arquivo de mensagem de commit não fornecido." >&2
  echo "Uso: $0 <caminho-do-arquivo>" >&2
  exit 1
fi

COMMIT_MSG_FILE="$1"

if [ ! -f "$COMMIT_MSG_FILE" ]; then
  echo "ERRO: Arquivo de mensagem de commit não encontrado: '$COMMIT_MSG_FILE'" >&2
  exit 1
fi

if [ ! -r "$COMMIT_MSG_FILE" ]; then
  echo "ERRO: Sem permissão de leitura para o arquivo: '$COMMIT_MSG_FILE'" >&2
  exit 1
fi

COMMENT_CHAR="#"
if command -v git >/dev/null 2>&1; then
  GIT_COMMENT_CHAR=$(git config --get core.commentChar 2>/dev/null || true)
  if [ -n "$GIT_COMMENT_CHAR" ] && [ "$GIT_COMMENT_CHAR" != "auto" ]; then
    COMMENT_CHAR="$GIT_COMMENT_CHAR"
  fi
fi

HEADER=""
FIRST_NON_EMPTY=""

while IFS= read -r line || [ -n "$line" ]; do
  cleaned_line="${line%$'\r'}"

  case "$cleaned_line" in
    "$COMMENT_CHAR"*)
      continue
      ;;
  esac

  if [ -z "$FIRST_NON_EMPTY" ]; then
    FIRST_NON_EMPTY="$cleaned_line"
    if [[ "$cleaned_line" =~ ^[[:space:]]*$ ]]; then
      continue
    fi
    HEADER="$cleaned_line"
    break
  fi
done < "$COMMIT_MSG_FILE"

if [ -z "$HEADER" ]; then
  echo "ERRO: O cabeçalho da mensagem de commit está vazio." >&2
  echo "Por favor, informe uma mensagem de commit válida." >&2
  exit 1
fi

TARGET_HEADER="$HEADER"
if [ "${COMMIT_LEGACY_PROFILE:-0}" = "1" ]; then
  if [[ "$TARGET_HEADER" =~ $LEGACY_PREFIX_REGEX ]]; then
    TARGET_HEADER="${TARGET_HEADER#"${BASH_REMATCH[0]}"}"
  fi
fi

if [[ "$TARGET_HEADER" =~ $STANDARD_REGEX ]]; then
  exit 0
fi

echo "================================================================================" >&2
echo "ERRO DE CONVENÇÃO: A mensagem de commit não segue o padrão adotado." >&2
echo "================================================================================" >&2
echo "Cabeçalho recebido:" >&2
echo "  \"$HEADER\"" >&2
echo "" >&2

if [[ "$HEADER" =~ ^(:[a-zA-Z0-9_+-]+:|[^[:alnum:][:space:]]+)[[:space:]]+ ]]; then
  echo "Motivo provável:" >&2
  echo "  Detectado emoji ou shortcode antes do tipo ('${BASH_REMATCH[0]}')." >&2
  echo "  No padrão adotado (Conventional Commits), o tipo deve iniciar o cabeçalho." >&2
  echo "  Para usar emoji, insira-o no início da descrição. Exemplo:" >&2
  echo "    feat: ✨ adicionar funcionalidade" >&2
elif [[ "$HEADER" =~ ^\[([a-zA-Z0-9_-]+)\][[:space:]]* ]]; then
  echo "Motivo provável:" >&2
  echo "  Detectado tipo entre colchetes ('${BASH_REMATCH[0]}')." >&2
  echo "  Colchetes não devem ser usados no tipo. Exemplo correto:" >&2
  echo "    ${BASH_REMATCH[1]}: descrição do commit" >&2
elif [[ "$HEADER" =~ ^([a-zA-Z0-9_-]+)\(\): ]]; then
  echo "Motivo provável:" >&2
  echo "  Escopo vazio detectado '()'. Se não houver escopo, omita os parênteses inteiramente." >&2
  echo "  Exemplo: '${BASH_REMATCH[1]}: descrição'" >&2
elif [[ "$HEADER" =~ ^([A-Z][a-zA-Z0-9_-]*)([\(:]) ]]; then
  echo "Motivo provável:" >&2
  echo "  O tipo '${BASH_REMATCH[1]}' possui letras maiúsculas. O tipo deve ser estritamente minúsculo." >&2
elif [[ "$HEADER" =~ ^init:|^🎉 ]]; then
  echo "Motivo provável:" >&2
  echo "  O tipo 'init' ou emoji isolado não é permitido diretamente." >&2
  echo "  Para o commit inicial, utilize: 'chore: iniciar projeto'." >&2
elif [[ "$HEADER" =~ ^([a-zA-Z0-9_-]+)(\([^\)]*\))?(!)?:\ *$ ]]; then
  echo "Motivo provável:" >&2
  echo "  A descrição está vazia ou contém apenas espaços em branco." >&2
elif [[ "$HEADER" =~ ^([a-zA-Z0-9_-]+)(\([^\)]*\))?(!)?:[[:space:]]{2,} ]]; then
  echo "Motivo provável:" >&2
  echo "  Há mais de um espaço após os dois-pontos ':'. Use exatamente um espaço ASCII." >&2
elif [[ "$HEADER" =~ [[:space:]]+$ ]]; then
  echo "Motivo provável:" >&2
  echo "  Espaço(s) em branco no final do cabeçalho (trailing spaces)." >&2
elif [[ ! "$HEADER" =~ : ]]; then
  echo "Motivo provável:" >&2
  echo "  Ausência de dois-pontos ':' separando o tipo/escopo da descrição." >&2
fi

echo "" >&2
echo "Formato esperado:" >&2
echo "  <tipo>[(escopo)][!]: <descrição>" >&2
echo "" >&2
echo "Tipos válidos:" >&2
echo "  feat, fix, docs, test, build, perf, style, refactor, chore, ci, raw, cleanup, remove, revert" >&2
echo "" >&2
echo "Exemplos válidos:" >&2
echo "  feat(auth): adicionar login" >&2
echo "  fix(api)!: alterar resposta de erro" >&2
echo "  docs: 📚 atualizar README" >&2
echo "  chore: iniciar projeto" >&2
echo "================================================================================" >&2

exit 1
