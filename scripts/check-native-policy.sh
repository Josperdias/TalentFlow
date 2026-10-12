#!/usr/bin/env bash
# Os apps Android/Windows devem ser NATIVOS: proíbe WebView, Capacitor, Cordova, TWA, Electron, WebView2.
set -euo pipefail
cd "$(dirname "$0")/.."
PATTERN='WebView|WebView2|Capacitor|Cordova|TrustedWebActivity|androidbrowserhelper|Electron|Microsoft\.Web\.WebView2|CoreWebView2|webkit\.WebView|ionic'
FOUND=$(grep -rIlE "$PATTERN" apps/android apps/windows --include='*.kt' --include='*.kts' --include='*.xml' --include='*.cs' --include='*.xaml' --include='*.csproj' --include='*.json' --include='*.toml' --include='*.gradle' --include='*.props' 2>/dev/null | grep -v '/build/' | grep -v '/bin/' | grep -v '/obj/' || true)
if [ -n "$FOUND" ]; then echo "ERRO: referências proibidas (cliente nativo não pode usar WebView/Electron):"; echo "$FOUND"; exit 1; fi
echo "OK: nenhum WebView/Electron/Capacitor/Cordova/TWA em apps/android e apps/windows."
