# TalentFlow People

Plataforma brasileira de recrutamento e gestão da jornada do colaborador, com **três clientes reais sobre a mesma API e o mesmo PostgreSQL**:

| Cliente | Tecnologia | Entregável | Estado |
|---|---|---|---|
| **Site** | React + TypeScript (Vite) | `talentflow-web-vX.Y.Z.zip` compilado, para o seu servidor | **validado**: 16/16 passos E2E em Chromium sobre o ZIP descompactado + API real + PostgreSQL |
| **Android** | Kotlin + Jetpack Compose (nativo) | `talentflow-android-vX.Y.Z-debug.apk` | veja `docs/STATUS.md` (build só roda no CI) |
| **Windows** | C# + WinUI 3 (nativo, sem navegador embutido) | `TalentFlow-Setup-vX.Y.Z.exe` + portátil `.zip` | veja `docs/STATUS.md` (build só roda no CI) |

> **Leia `docs/STATUS.md` antes de usar.** Ele diz com precisão o que foi testado, o que é parcial e o que não foi feito.
> Pré-lançamento: não use com dados pessoais reais sem a revisão de segurança descrita lá.

Não há WebView, Electron, Capacitor, Cordova nem site embrulhado: o CI **falha** se qualquer cliente nativo referenciar isso
(`scripts/check-native-policy.sh`) e inspeciona o APK e a publicação do Windows.

## Links
- **Abrir o site no servidor próprio:** definido por você. Informe a URL em `PUBLIC_WEB_URL` (nenhum endereço foi inventado). Veja `apps/web/deploy/DEPLOY-WEB.md`.
- **Downloads (APK, instalador Windows, site, checksums):** página *Releases* deste repositório (rascunho até você autorizar a publicação).
- Capturas reais: `docs/screenshots/`.

## Mesmo dado em todo lugar
Criar uma vaga no Android -> aparece no site e no Windows; mover candidatura no Windows -> aparece no site e no Android; editar em dois
lugares ao mesmo tempo -> o segundo recebe **conflito** (nada é sobrescrito em silêncio). Isto é verificado por testes que usam dois
"aparelhos" contra a API real (Kotlin e C#) e pelo E2E do site com um segundo cliente alterando o servidor. Detalhes: `docs/ARQUITETURA.md`.

## Começar (desenvolvimento)
```bash
# API + PostgreSQL real, sem Docker
scripts/dev-pg.sh start
cd services/api && pip install -r requirements-dev.txt
export TF_TEST_DATABASE_URL=$(../../scripts/dev-pg.sh url) && python -m pytest -q      # 35 testes

# Site: build, ZIP e E2E completo (banco novo -> migrações -> API -> site -> Chromium)
scripts/package-web.sh && scripts/e2e-web.sh

# Android (só :core localmente; o APK compila no CI)
cd apps/android && ./gradlew -PcoreOnly=true :core:test
# Windows (Core em qualquer SO com .NET 8; o app WinUI compila no CI windows-latest)
cd apps/windows && dotnet test TalentFlow.Core.Tests
```
Contas de demonstração (somente desenvolvimento, senha `Demo@2026!`): `admin@nexa.demo`, `recrutador@nexa.demo`, `gestor@nexa.demo`,
`entrevistador@nexa.demo`, `candidato@nexa.demo`, `admin@orbe.demo` (outra empresa, para testar isolamento). **Produção não tem contas de demonstração.**

## Instalar para valer
`docs/DEPLOY-SERVIDOR.md` (API + PostgreSQL em contêineres, backup/restore, HTTPS) e `apps/web/deploy/DEPLOY-WEB.md` (site).

## Estrutura
```text
services/api/  FastAPI, Alembic, testes        apps/android/  Kotlin: :core + :app (Compose)
apps/web/      React/TS + deploy + E2E         apps/windows/  C#: Core + testes + WinUI 3 + instalador
packages/      design-tokens, contracts        infra/         docker-compose, backup, restore
scripts/       empacotar, E2E, políticas       docs/          arquitetura, design, status, ADRs
```

## GitHub
CI em todo push/PR (`ci`, `android`, `windows`), `release` (gera **rascunho** de Release com checksums) e `auto-merge` (usa o recurso
nativo do GitHub e só conclui depois de aprovação e checks obrigatórios). Configure uma vez: `scripts/setup-github.sh Josperdias/TalentFlow`.
Pendências de configuração do repositório estão em `docs/STATUS.md`.

## Licenças e referências
Código próprio. Inspirações de padrões (Greenhouse, Workday, Frappe HR) sem copiar código ou interface; nenhum código GPL/AGPL foi incorporado.
Fontes do site: IBM Plex e Source Serif 4 (SIL OFL), empacotadas no ZIP.
