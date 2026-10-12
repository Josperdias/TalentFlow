#!/usr/bin/env bash
# E2E completo do pacote web: banco PostgreSQL NOVO -> migrações Alembic -> API -> servidor estático -> Chromium.
# Uso: scripts/e2e-web.sh [pasta-dist=apps/web/dist] [pasta-capturas=docs/screenshots]
# Requer um PostgreSQL acessível: defina TF_E2E_ADMIN_URL (ex.: postgresql://postgres@127.0.0.1:5432/postgres)
# ou deixe vazio para usar scripts/dev-pg.sh (cluster local descartável).
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
DIST=${1:-$ROOT/apps/web/dist}; SHOTS=${2:-$ROOT/docs/screenshots}
for port in 8000 8080; do
  if (exec 3<>/dev/tcp/127.0.0.1/$port) 2>/dev/null; then echo "ERRO: porta $port já está em uso; encerre o processo antes de rodar o E2E." >&2; exit 2; fi
done
DB="tf_e2e_$(date +%s)"
if [ -z "${TF_E2E_ADMIN_URL:-}" ]; then
  "$ROOT/scripts/dev-pg.sh" start >/dev/null; ADMIN="postgresql://postgres@127.0.0.1:${TF_PGPORT:-54329}/postgres"
else ADMIN=$TF_E2E_ADMIN_URL; fi
psql "$ADMIN" -qc "create database $DB"
BASE=${ADMIN%/*}; export DATABASE_URL="postgresql+psycopg://${BASE#postgresql://}/$DB"
cleanup(){ [ -n "${API_PID:-}" ] && kill $API_PID 2>/dev/null || true; [ -n "${SITE_PID:-}" ] && kill $SITE_PID 2>/dev/null || true; psql "$ADMIN" -qc "drop database if exists $DB" 2>/dev/null || true; }
trap cleanup EXIT
cd "$ROOT/services/api"
alembic upgrade head >/dev/null
APP_ENV=development DEMO_SEED=true SERVE_LEGACY_WEB=false TF_LOGIN_IP_LIMIT=100000 \
  python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 >/tmp/tf-e2e-api.log 2>&1 & API_PID=$!
for i in $(seq 1 40); do curl -sf http://127.0.0.1:8000/api/v1/health >/dev/null && break; sleep 0.5; done
node "$ROOT/scripts/serve-dist.mjs" "$DIST" 8080 http://127.0.0.1:8000 >/tmp/tf-e2e-site.log 2>&1 & SITE_PID=$!
sleep 1
python3 -I "$ROOT/apps/web/e2e/e2e_web.py" http://127.0.0.1:8080 "$SHOTS"
