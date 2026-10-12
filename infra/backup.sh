#!/usr/bin/env bash
# Backup do PostgreSQL (dump comprimido) com rotação. Uso: ./backup.sh [dias-de-retenção=14]. Agende no cron (diário).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p backups; KEEP=${1:-14}; STAMP=$(date +%Y%m%d-%H%M%S)
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "backups/talentflow-$STAMP.dump"
find backups -name 'talentflow-*.dump' -mtime +"$KEEP" -delete
echo "Backup gravado em infra/backups/talentflow-$STAMP.dump (guarde uma cópia FORA deste servidor)."
