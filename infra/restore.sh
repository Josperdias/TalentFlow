#!/usr/bin/env bash
# Restaura um backup (SUBSTITUI os dados atuais). Uso: ./restore.sh backups/talentflow-AAAAMMDD-HHMMSS.dump
set -euo pipefail
cd "$(dirname "$0")"
[ -f "${1:-}" ] || { echo "Informe o arquivo .dump"; exit 1; }
read -r -p "Isto APAGA os dados atuais e restaura $1. Digite RESTAURAR para continuar: " ok
[ "$ok" = "RESTAURAR" ] || { echo "Cancelado."; exit 1; }
docker compose stop api
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < "$1"
docker compose start api
echo "Restauração concluída."
