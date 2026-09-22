#!/usr/bin/env bash
set -e

GIT_DIR=$(git rev-parse --git-dir 2>/dev/null || true)
if [ -z "$GIT_DIR" ]; then
  echo "ERRO: O diretório atual não é um repositório Git válido." >&2
  exit 1
fi

GIT_ROOT=$(git rev-parse --show-toplevel)
cd "$GIT_ROOT"

MANIFEST="$GIT_DIR/commit-hooks-manifest.json"
PREV_HOOKSPATH=""

if [ -f "$MANIFEST" ]; then
  PREV_HOOKSPATH=$(grep '"previous_core_hookspath"' "$MANIFEST" | head -n1 | sed -E 's/.*"previous_core_hookspath": *"([^"]*)".*/\1/')
fi

if [ -n "$PREV_HOOKSPATH" ]; then
  git config --local core.hooksPath "$PREV_HOOKSPATH"
  echo "INFO: core.hooksPath restaurado para a configuração anterior: '$PREV_HOOKSPATH'."
else
  git config --local --unset core.hooksPath 2>/dev/null || true
  echo "INFO: core.hooksPath local removido (restaurando comportamento padrão do Git)."
fi

if [ -f "$MANIFEST" ]; then
  rm -f "$MANIFEST"
fi

echo "SUCESSO: Desinstalação do hook concluída com sucesso."
echo "Observação: Os scripts em 'scripts/commits/' e '.githooks/' foram mantidos intactos."
echo "Caso deseje excluí-los manualmente, verifique se não fez alterações antes de apagá-los."
