#!/usr/bin/env bash
# Gera dist/talentflow-web-v<VERSION>.zip (site compilado + guia + exemplos + checksum).
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); VER=$(cat "$ROOT/VERSION")
cd "$ROOT/apps/web"
[ -d node_modules ] || npm ci --no-audit --no-fund
npm run build >/dev/null
STAGE=$(mktemp -d); trap 'rm -rf "$STAGE"' EXIT
cp -r dist/. "$STAGE"/
cp deploy/DEPLOY-WEB.md deploy/nginx.conf.example deploy/htaccess.example "$STAGE"/
echo "$VER" > "$STAGE/VERSION"
mkdir -p "$ROOT/dist"; OUT="$ROOT/dist/talentflow-web-v$VER.zip"; rm -f "$OUT"
(cd "$STAGE" && zip -qr -X "$OUT" .)
(cd "$ROOT/dist" && sha256sum "talentflow-web-v$VER.zip" > "talentflow-web-v$VER.zip.sha256")
unzip -tq "$OUT" && echo "$OUT" && cat "$OUT.sha256" && unzip -l "$OUT" | tail -1
