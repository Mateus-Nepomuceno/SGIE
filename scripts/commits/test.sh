#!/usr/bin/env bash
# ==============================================================================
# scripts/commits/test.sh
# Suíte de testes automatizados: unitários e de integração em repositório temporário
# ==============================================================================
set -e

GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
VALIDATOR="$GIT_ROOT/scripts/commits/validate-message.sh"
TEMP_BASE=$(mktemp -d 2>/dev/null || mktemp -d -t 'committest')
trap 'rm -rf "$TEMP_BASE"' EXIT

echo "================================================================================"
echo "INICIANDO BATERIA DE TESTES DO VALIDADOR DE COMMITS"
echo "Diretório de trabalho temporário: $TEMP_BASE"
echo "================================================================================"

FAILED=0
PASSED=0

assert_valid() {
  local desc="$1"
  local content="$2"
  local file="$TEMP_BASE/test_valid.txt"
  printf "%b\n" "$content" > "$file"

  local hash_before
  hash_before=$(sha256sum "$file" | cut -d' ' -f1)

  if bash "$VALIDATOR" "$file" >/dev/null 2>&1; then
    local hash_after
    hash_after=$(sha256sum "$file" | cut -d' ' -f1)
    if [ "$hash_before" != "$hash_after" ]; then
      echo "FALHA (arquivo alterado): $desc"
      FAILED=$((FAILED + 1))
    else
      echo "PASS: $desc"
      PASSED=$((PASSED + 1))
    fi
  else
    echo "FALHA (rejeitado indevidamente): $desc"
    FAILED=$((FAILED + 1))
  fi
}

assert_invalid() {
  local desc="$1"
  local content="$2"
  local file="$TEMP_BASE/test_invalid.txt"
  printf "%b\n" "$content" > "$file"

  if bash "$VALIDATOR" "$file" >/dev/null 2>&1; then
    echo "FALHA (aceito indevidamente): $desc"
    FAILED=$((FAILED + 1))
  else
    echo "PASS (rejeitado como esperado): $desc"
    PASSED=$((PASSED + 1))
  fi
}

echo ""
echo "--- 1. TESTES UNITÁRIOS DE MENSAGENS VÁLIDAS ---"
assert_valid "feat padrão com escopo" "feat(auth): adicionar login"
assert_valid "fix com escopo e breaking change !" "fix(api)!: alterar resposta de erro\n\nSubstitui o campo error pelo campo errors.\n\nBREAKING CHANGE: consumidores devem ler o campo errors.\nRefs: #133"
assert_valid "feat sem ! com BREAKING CHANGE no rodapé" "feat(api): alterar contrato\n\nBREAKING CHANGE: o campo legado foi removido."
assert_valid "docs com emoji na descrição e rodapé multilinha" "docs: 📚 atualizar README\n\nExplica a instalação local e o procedimento de rollback.\n\nReviewed-by: Pessoa Revisora\nRefs: #133"
assert_valid "tipo raw" "raw: atualizar dados de configuração"
assert_valid "tipo cleanup" "cleanup: remover comentários obsoletos no módulo de auth"
assert_valid "tipo remove" "remove: excluir arquivo legado obsoleto"
assert_valid "tipo revert" "revert: desfazer alteração anterior no serializer"
assert_valid "tipo test" "test(unit): adicionar testes de regressão"
assert_valid "tipo build" "build: atualizar dependências no poetry"
assert_valid "tipo perf" "perf: otimizar consulta ao banco de dados"
assert_valid "tipo style" "style: corrigir identação no arquivo"
assert_valid "tipo refactor" "refactor: simplificar lógica de parsing"
assert_valid "tipo chore (inicial)" "chore: iniciar projeto"
assert_valid "tipo ci" "ci: ajustar workflow de validação"
assert_valid "comentários de template ignorados no início" "# Comentário inicial do Git\nfeat(core): carregar módulos sob demanda\n# Linha final"
assert_valid "terminação CRLF tratada na leitura" "feat(core): suporte a CRLF\r\n\r\nCorpo da mensagem\r\n"
assert_valid "arquivo sem newline final" "feat: mensagem sem newline"
assert_valid "descrição em português e caracteres acentuados" "fix: correção de validação de pontuação e acentuação: maçã & ação"

echo ""
echo "--- 2. TESTES UNITÁRIOS DE MENSAGENS INVÁLIDAS ---"
assert_invalid "prefixo de emoji antes do tipo" ":sparkles: feat: adicionar login"
assert_invalid "emoji direto antes do tipo" "✨ feat: adicionar login"
assert_invalid "formato push.sh original [tipo] emoji: msg" "[feat] ✨: adicionar login"
assert_invalid "tipo com maiúscula" "Feat: adicionar login"
assert_invalid "tipo feature inexistente" "feature: adicionar login"
assert_invalid "escopo vazio ()" "feat(): adicionar login"
assert_invalid "dois-pontos sem descrição" "feat(auth):"
assert_invalid "apenas espaços após dois-pontos" "feat:   "
assert_invalid "espaço duplo após dois-pontos" "feat:  adicionar login"
assert_invalid "mensagem sem tipo (texto livre)" "corrigir bug no checkout"
assert_invalid "espaço no final da linha (trailing whitespace)" "chore: ajustar rotina "
assert_invalid "commit inicial com emoji isolado" "🎉 Commit inicial"
assert_invalid "tipo init inexistente" "init: iniciar projeto"
assert_invalid "arquivo vazio" ""
assert_invalid "arquivo apenas com comentários" "# Comentário 1\n# Comentário 2\n"
assert_invalid "múltiplos pontos de exclamação" "feat(auth)!!: alterar login"
assert_invalid "escopo com caracteres inválidos" "feat(auth/v2): rota de login"

echo ""
echo "--- 3. TESTES DE TRATAMENTO DE ARQUIVO E ERROS DE ENTRADA ---"
if bash "$VALIDATOR" >/dev/null 2>&1; then
  echo "FALHA: Validador aceitou chamada sem argumentos"
  FAILED=$((FAILED + 1))
else
  echo "PASS: Chamada sem argumentos rejeitada com erro"
  PASSED=$((PASSED + 1))
fi

if bash "$VALIDATOR" "$TEMP_BASE/inexistente.txt" >/dev/null 2>&1; then
  echo "FALHA: Validador aceitou arquivo inexistente"
  FAILED=$((FAILED + 1))
else
  echo "PASS: Arquivo inexistente rejeitado com erro"
  PASSED=$((PASSED + 1))
fi

echo ""
echo "--- 4. TESTE DO PERFIL LEGADO (OPT-IN) ---"
LEGACY_FILE="$TEMP_BASE/legacy.txt"
printf ":sparkles: feat(auth): adicionar login legado\n" > "$LEGACY_FILE"
if COMMIT_LEGACY_PROFILE=1 bash "$VALIDATOR" "$LEGACY_FILE" >/dev/null 2>&1; then
  echo "PASS: Perfil legado aceitou prefixo quando COMMIT_LEGACY_PROFILE=1"
  PASSED=$((PASSED + 1))
else
  echo "FALHA: Perfil legado deveria ter aceito o prefixo"
  FAILED=$((FAILED + 1))
fi

echo ""
echo "--- 5. TESTES DE INTEGRAÇÃO EM REPOSITÓRIO GIT TEMPORÁRIO ---"
DISPOSABLE_REPO="$TEMP_BASE/repositorio com espacos"
mkdir -p "$DISPOSABLE_REPO"
cd "$DISPOSABLE_REPO"

git init -q
git config user.name "Test Runner"
git config user.email "test@example.com"

mkdir -p .githooks scripts/commits
cp "$GIT_ROOT/.githooks/commit-msg" .githooks/commit-msg
cp "$GIT_ROOT/scripts/commits/validate-message.sh" scripts/commits/validate-message.sh
cp "$GIT_ROOT/scripts/commits/install.sh" scripts/commits/install.sh
cp "$GIT_ROOT/scripts/commits/uninstall.sh" scripts/commits/uninstall.sh
chmod +x .githooks/commit-msg scripts/commits/*.sh

# Instalação inicial
bash scripts/commits/install.sh >/dev/null 2>&1
echo "PASS: Instalação em repositório temporário concluída"
PASSED=$((PASSED + 1))

# Idempotência
IDEMPOTENT_OUT=$(bash scripts/commits/install.sh 2>&1)
if [[ "$IDEMPOTENT_OUT" =~ "no-op" ]]; then
  echo "PASS: Idempotência confirmada na segunda instalação"
  PASSED=$((PASSED + 1))
else
  echo "FALHA: Segunda instalação não resultou em no-op"
  FAILED=$((FAILED + 1))
fi

# Commit válido
echo "teste" > teste.txt
git add teste.txt
if git commit -m "feat(integracao): validar commit real via hook" >/dev/null 2>&1; then
  echo "PASS: Commit real válido aceito pelo Git hook"
  PASSED=$((PASSED + 1))
else
  echo "FALHA: Commit válido foi rejeitado pelo hook"
  FAILED=$((FAILED + 1))
fi

# Commit inválido
echo "outro" >> teste.txt
git add teste.txt
HEAD_ANTES=$(git rev-parse HEAD)
if git commit -m "commit invalido sem padrao" >/dev/null 2>&1; then
  echo "FALHA: Commit inválido foi aceito indevidamente"
  FAILED=$((FAILED + 1))
else
  HEAD_DEPOIS=$(git rev-parse HEAD)
  if [ "$HEAD_ANTES" = "$HEAD_DEPOIS" ]; then
    echo "PASS: Commit inválido bloqueado com sucesso; nenhum commit criado"
    PASSED=$((PASSED + 1))
  else
    echo "FALHA: HEAD foi modificado apesar do erro no commit"
    FAILED=$((FAILED + 1))
  fi
fi

# Execução a partir de subdiretório
mkdir -p sub/dir
cd sub/dir
echo "sub" > sub.txt
git add sub.txt
if git commit -m "chore(infra): commit executado de subdiretorio" >/dev/null 2>&1; then
  echo "PASS: Hook executado a partir de subdiretório com sucesso"
  PASSED=$((PASSED + 1))
else
  echo "FALHA: Execução a partir de subdiretório falhou"
  FAILED=$((FAILED + 1))
fi
cd "$DISPOSABLE_REPO"

# Desinstalação e restauração
bash scripts/commits/uninstall.sh >/dev/null 2>&1
RESTORED_HOOKSPATH=$(git config --local --get core.hooksPath 2>/dev/null || echo "UNSET")
if [ "$RESTORED_HOOKSPATH" = "UNSET" ]; then
  echo "PASS: Desinstalação removeu core.hooksPath com sucesso"
  PASSED=$((PASSED + 1))
else
  echo "FALHA: core.hooksPath ainda configurado após desinstalação"
  FAILED=$((FAILED + 1))
fi

echo ""
echo "================================================================================"
echo "RESULTADOS FINAIS DA SUÍTE DE TESTES:"
echo "Testes com sucesso: $PASSED"
echo "Testes com falha:   $FAILED"
echo "================================================================================"

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi

exit 0
