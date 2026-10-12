#!/usr/bin/env bash
# Falha se o repositório contiver chaves privadas, keystores ou credenciais óbvias.
set -euo pipefail
cd "$(dirname "$0")/.."
BAD=$(git ls-files | grep -E '\.(jks|keystore|pfx|p12|pem|key)$' || true)
HITS=$(git grep -InE '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|xox[baprs]-[A-Za-z0-9-]{10,})' -- . ':!scripts/check-no-secrets.sh' || true)
if [ -n "$BAD$HITS" ]; then echo "ERRO: possíveis segredos versionados:"; echo "$BAD"; echo "$HITS"; exit 1; fi
echo "OK: nenhum segredo óbvio versionado."
