#!/bin/sh
# Aplica as migrações (idempotente) e só então sobe a API.
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
