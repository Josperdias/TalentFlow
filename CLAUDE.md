# Continuidade (Claude / ChatGPT / pessoas)

Leia nesta ordem: `docs/STATUS.md` -> `docs/ARQUITETURA.md` -> `docs/INVENTARIO-LEGADO.md` -> `docs/adr/`.
Origem e missão: pasta do Google Drive do projeto (`CLAUDE-MISSAO-v1.3.md`, `README-TalentFlow-v1.3.md`, `PACOTES-E-DEPLOY-v1.3.md`).
**Não recomece o projeto.** Não afirme o que não foi executado: registre teste, número e ambiente.

## Regras que valem sempre
1. RBAC, escopo por empresa e regras de negócio ficam **no servidor**; cliente nunca é a proteção.
2. Escritas usam `If-Match`; 409 vira diálogo de conflito. Nunca sobrescrever em silêncio. Edição presa à versão aberta.
3. "Sem dado" é `—`, nunca `0`. Sem simulação offline: sem rede mostra "Sem conexão".
4. Sem WebView/Electron/Capacitor/Cordova/TWA. `scripts/check-native-policy.sh` garante.
5. Segredos nunca no repositório, no ZIP do site, nos apps ou no Drive. Keystore e certificados só em GitHub Secrets.
6. Instrumentos comportamentais não validados **não** geram diagnóstico nem decisão automática.
7. Tokens de design vêm de `packages/design-tokens/tokens.json` (`node packages/design-tokens/build.mjs`); não edite os arquivos gerados.
8. Mudou a API? Rode `python scripts/export-openapi.py` e atualize os dois `Core` (Kotlin e C#) + testes de integração.

## Comandos
- API: `scripts/dev-pg.sh start`; `cd services/api && TF_TEST_DATABASE_URL=$(../../scripts/dev-pg.sh url) python -m pytest -q`
- Migração nova: `alembic revision --autogenerate -m "..."`; revise, `alembic check`, suba/desça/suba.
- Site: `cd apps/web && npm ci && npm run build && npm test`; E2E: `scripts/e2e-web.sh` (banco novo a cada execução).
- Android local: `./gradlew -PcoreOnly=true :core:test` (o `:app` exige o AGP; roda só no CI). Integração real: `TF_API_URL=http://127.0.0.1:8000`.
- Windows local: `dotnet test apps/windows/TalentFlow.Core.Tests` (idem `TF_API_URL`). O app WinUI só compila no CI.

## Armadilhas já encontradas (não repita)
- `pkill -f` pode casar com a própria linha do comando e derrubar o shell: use PID.
- `conftest` forçando SQLite fazia a suíte "passar em PostgreSQL" sem tocar o PostgreSQL. Confirme com contagem de linhas.
- Banco acumulado entre rodadas de E2E esconde bugs e cria falhas falsas: use `scripts/e2e-web.sh` (banco novo).
- Proxy que reescreve `Host` quebra o login ("Origem inválida"): repasse o Host ou defina `TRUSTED_ORIGINS`.
- WinUI: dentro de `namespace TalentFlow.Windows`, `Windows.UI...` resolve para o namespace do projeto; use `global::Windows...`.
- WinUI: não use `Frame.Navigate` com páginas só em C# (sem XAML); instancie direto.
- Gradle/AGP: declare o AGP na raiz (`apply false`) senão o Kotlin Android não enxerga `BaseVariant`.
- YAML de workflow: `: ` dentro de `name:` sem aspas invalida o arquivo inteiro. Valide antes de dar push.
