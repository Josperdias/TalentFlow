#!/usr/bin/env bash
# Configura o repositório: proteção da branch main, revisão obrigatória, checks obrigatórios, auto-merge.
# Execute UMA vez, como dono do repositório, com a GitHub CLI autenticada:  gh auth login
# Uso: scripts/setup-github.sh Josperdias/TalentFlow
set -euo pipefail
REPO=${1:?Informe dono/repositorio, ex.: Josperdias/TalentFlow}

echo "1) Permitir auto-merge e apagar branches mescladas"
gh api -X PATCH "repos/$REPO" -F allow_auto_merge=true -F delete_branch_on_merge=true -F allow_squash_merge=true -F allow_merge_commit=false -F allow_rebase_merge=false >/dev/null

echo "2) Proteger a branch main"
gh api -X PUT "repos/$REPO/branches/main/protection" --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "policy (sem WebView/Electron/segredos)",
      "api (PostgreSQL 16)",
      "web (build, testes, E2E em navegador)",
      "compose (servidor em contêineres - subir, provisionar, backup/restore)",
      "core (testes unitários + integração com API real)",
      "apk (debug nativo Kotlin/Compose)",
      "core C# (testes unitários + integração com API real)",
      "app WinUI 3 (publish autossuficiente + instalador .exe)"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "require_last_push_approval": true
  },
  "required_conversation_resolution": true,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "restrictions": null
}
JSON

echo "3) Rótulo usado pelo workflow auto-merge"
gh label create automerge --repo "$REPO" --color 0B4F5C --description "Habilita auto-merge após revisões e checks" 2>/dev/null || true
echo "Pronto. O auto-merge só conclui após: 1 aprovação de code owner + todos os checks verdes + conversas resolvidas."
