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
CURRENT_LOCAL_HOOKSPATH=$(git config --local --get core.hooksPath 2>/dev/null || true)

if [ "$CURRENT_LOCAL_HOOKSPATH" = ".githooks" ] && [ -f "$MANIFEST" ]; then
  echo "INFO: core.hooksPath já está configurado para '.githooks'. Instalação já ativa (no-op)."
  chmod +x .githooks/commit-msg scripts/commits/*.sh 2>/dev/null || true
  exit 0
fi

if [ -n "$CURRENT_LOCAL_HOOKSPATH" ] && [ "$CURRENT_LOCAL_HOOKSPATH" != ".githooks" ]; then
  if [ "$1" != "--force" ]; then
    echo "ERRO DE CONFLITO: core.hooksPath local já está definido como '$CURRENT_LOCAL_HOOKSPATH'." >&2
    echo "Para forçar a substituição mantendo backup, reexecute com: bash scripts/commits/install.sh --force" >&2
    exit 1
  fi
  echo "AVISO: Substituindo configuração anterior '$CURRENT_LOCAL_HOOKSPATH' sob demanda (--force)."
fi

HASH_HOOK=$(sha256sum .githooks/commit-msg 2>/dev/null | cut -d' ' -f1 || echo "unknown")
HASH_VALIDATOR=$(sha256sum scripts/commits/validate-message.sh 2>/dev/null | cut -d' ' -f1 || echo "unknown")

cat <<EOF > "$MANIFEST"
{
  "installed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "previous_core_hookspath": "$CURRENT_LOCAL_HOOKSPATH",
  "files": {
    ".githooks/commit-msg": "$HASH_HOOK",
    "scripts/commits/validate-message.sh": "$HASH_VALIDATOR"
  }
}
EOF

git config --local core.hooksPath .githooks

chmod +x .githooks/commit-msg scripts/commits/*.sh 2>/dev/null || true

echo "SUCESSO: Hooks de validação de commit ativados com sucesso em .githooks."
echo "Manifesto de instalação registrado em '$MANIFEST'."
