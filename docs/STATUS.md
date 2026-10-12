# Estado real do projeto (v1.3.0-rc.1, 2026-10-12)

Este documento é a fonte de verdade sobre **o que existe, o que foi testado e o que falta**. Se algo aqui contradizer um README
ou um relatório, vale o que está aqui. Números vêm de execuções reais, com o ambiente indicado.

## Resumo em uma tabela

| Entrega | Estado | Evidência |
|---|---|---|
| API v1 sobre PostgreSQL | **pronta para teste**; não auditada | 36 testes (PG 16 real e SQLite); CI verde |
| Migrações Alembic | **validadas** | subir/`check`/descer/subir; upgrade de banco v1.2 **com dados** |
| Site (ZIP compilado) | **validado** | E2E 16/16 em Chromium, sobre o ZIP descompactado, API e PG reais (local e CI) |
| Android nativo (Kotlin/Compose) | APK de **depuração** compila no CI; teste de interface em emulador **em diagnóstico** | `:core` testado; ver "Android" |
| Windows nativo (C#/WinUI 3) | **compila, publica e gera instalador no CI** (não assinado); nunca usado por uma pessoa | `Core` testado; instalador 42 MB + zip portátil 62 MB com SHA-256 (run 38299557063) |
| Servidor em contêineres | **validado no CI** (job `compose`: subir, provisionar admin, login, backup, apagar, restaurar) | CI verde |
| GitHub: CI, release (rascunho), auto-merge | workflows prontos e executando | **proteção de `main` NÃO configurada** (ver pendências) |
| Releases publicadas | **nenhuma** | nada foi publicado; a Release nasce como rascunho |
| Site publicado no seu domínio | **não** | você ainda não informou domínio nem hospedagem |

## O que foi realmente executado

| Teste | Quantidade / resultado | Ambiente |
|---|---|---|
| API pytest (18 herdados + 18 novos) | 36 aprovados | PostgreSQL 16.15 local e GitHub `ubuntu-latest` + serviço PG 16; também SQLite |
| Baseline v1.2 antes de mexer | 18/18 em SQLite; **em PostgreSQL passou a rodar de verdade só agora** (o `conftest` forçava SQLite) | local |
| Alembic | `0001` (schema v1.2) -> `0002`; ciclo completo; `alembic check` sem deriva | PG 16 local e CI |
| Produção (`APP_ENV=production`) | recusa subir sem migrações; sem HTML, sem `/workspace`, sem contas demo; login do 1º admin criado por script | local |
| Site: vitest | 5 | local e CI |
| Site: E2E em navegador | 16/16: login/erro, sessão após recarregar, pipeline, **mudança de outro cliente aparece sem recarregar**, **conflito não sobrescreve**, PDI, ausências, logout, papéis (gestor, candidato), celular 390 px sem rolagem horizontal, servidor inalcançável | Chromium; local sobre `dist/` e sobre o **ZIP descompactado**; CI |
| Kotlin `:core` | 13 unitários + 3 contra a **API real** (login/isolamento, A cria -> B enxerga + conflito 409, refresh rotativo) | JVM local e CI |
| C# `Core` | 20 unitários + 3 contra a **API real** (mesmos cenários) | .NET 8 local e CI |
| Política "sem WebView/Electron/segredos" | verde | CI |

## Identidade visual "Aurora" (a pedido: mais próxima do protótipo, mais premium)
- **Site:** reescrito e **visto em capturas reais** (Chromium, `docs/screenshots/`): menu lateral navy, barra superior, indicadores com cor de
  significado, funil animado, rosca SVG, pipeline com avatares, login com fundo animado, diálogos com "pop". E2E 16/16 mantido.
  Contraste AA conferido por script (`check-contrast.mjs`, roda no CI). Dark mode: tokens existem, **não revisado visualmente**.
- **Android e Windows:** mesmo vocabulário (tokens, fontes Plus Jakarta Sans + Fraunces embutidas, formas, gradientes, animações de entrada,
  rosca e barras animadas). **Só compilam no CI e eu não vi nenhuma tela deles**: o ajuste fino de espaçamento/tipografia nesses dois
  depende de você abrir o app e apontar o que destoa. No Windows, as fontes são carregadas por `ms-appx:///` e, se o Windows não
  resolver o arquivo, a interface cai para Segoe UI (não quebra, mas perde a tipografia). Isso **não foi verificado em máquina Windows**.
- **Ainda não há:** gráfico de evolução temporal (a API não fornece série histórica; não vamos inventar), dark mode revisado, ilustrações.

## Android
- **Feito e testado:** `:core` (cliente HTTP, refresh, `If-Match`/409, feed de sync) em JVM, local e CI, incluindo a API real.
- **Escrito, compilação só no CI:** `:app` (Compose): servidor configurável, login, visão geral, vagas + pipeline com mover/editar,
  candidatos, pessoas (colaboradores, PDI, ausências), conta/sessões, portal do candidato; tokens no Android Keystore (AES-GCM).
- **Por que não compilei aqui:** o ambiente bloqueia `dl.google.com` (AGP/androidx). Cada erro de compilação só aparece no CI.
- **Nunca executado em aparelho ou emulador.** Não há captura de tela real do app Android. Login e sincronização no Android foram
  provados na camada `:core`, **não** na interface.
- Assinatura: o APK de release assinado só é gerado se os segredos `TF_KEYSTORE_BASE64`, `TF_KEYSTORE_PASSWORD`, `TF_KEY_ALIAS`,
  `TF_KEY_PASSWORD` existirem. **Não existem**; portanto só o APK de **depuração** (rotulado) é gerado.
- R8/minify está desligado até haver teste em aparelho. `minSdk 26` (Android 8.0), `targetSdk 35`.

## Windows
- **Feito e testado:** `TalentFlow.Core` (mesmos cenários do Kotlin), local e CI.
- **Compilado no CI (`windows-latest`)** — app WinUI 3 *unpackaged*, autossuficiente, interface em C# com os tokens do design system,
  tokens de sessão cifrados com DPAPI. Resultado do run 38299557063: publicação OK; instalador Inno Setup
  `TalentFlow-Setup-v1.3.0-rc.1.exe` (42 MB) e pacote portátil `.zip` (62 MB) gerados, cada um com `.sha256`.
- **Sem navegador embutido:** nosso código não referencia WebView2/Electron (varredura de fontes limpa). O `Microsoft.Web.WebView2.*` que
  aparece em metadados vem da projeção do Windows App SDK; os binários do WebView2 são removidos do pacote e o app ainda abre.
- **Teste de fumaça:** o workflow abre o app, captura a tela e fecha (passo marcado `continue-on-error`; uma captura foi anexada ao
  artefato). Eu **não vi** essa captura (o ambiente não consegue baixar artefatos) e isso **não** substitui teste manual.
- **Nunca usado por uma pessoa, nem contra um servidor real pela interface.** Sem certificado de código: o instalador **não é
  assinado** e o SmartScreen avisará "editor desconhecido".

## Parcial, simulado ou ausente (inventário honesto)

| Item | Situação |
|---|---|
| OAuth2/OIDC Authorization Code + PKCE no navegador do sistema | **não implementado**; login nativo usa formulário próprio -> `/auth/token` |
| Auto-atualização dos apps (manifesto assinado) | **não implementado**; só aviso de versão mínima via `/health` |
| Sincronização em tempo real (SSE/WebSocket) | **não**; polling de 4-5 s |
| Offline com fila de mutações | **não** (por desenho: mostra "sem conexão") |
| Row-Level Security no PostgreSQL | **não**; isolamento só na aplicação (coberto por testes) |
| MFA, retenção automática de dados, direitos do titular (LGPD) | **não** |
| `/api/v1/public/jobs` | **corrigido**: exige o slug da empresa; uma empresa não lista as vagas das outras (a rota antiga `/api/public/jobs` segue só em desenvolvimento) |
| Competências/GAP, ciclos 90/180/360, calibração, mobilidade, questionários, governança | **não migrados** (existiam só no snapshot JSONB v1.1) |
| People Analytics com coortes, catálogo de fórmulas e drill-down | **parcial**: boletim e funil reais; sem coortes |
| Entrevistas, scorecards, propostas, onboarding, currículos | **só na API**; sem tela nos três clientes |
| Nova solicitação de ausência | só no site |
| Exportação CSV/XLSX/PDF | **não** |
| E-mail e WhatsApp | **simulados** (fila no banco, nada é enviado) |
| IA de "fit" | heurística local revisável; sem LLM |
| Gráficos interativos | funil em barras (estático); sem gráficos interativos |
| Dark mode | tokens existem; **não testado visualmente** no site |
| Acessibilidade | contraste calculado; **sem** axe/Lighthouse/leitor de tela |
| Geração de SDKs a partir do OpenAPI | **não**; modelos escritos à mão, protegidos por testes reais |
| Docker Compose no ambiente local | **não testado** (sem daemon); testado no CI (job `compose`) |
| Nginx/Apache do exemplo | **não validados** em hospedagem real |
| Site em subpasta | desenhado para funcionar (HashRouter + `base './'`), **não testado** em subpasta real |

## Pendências que dependem do dono do repositório
1. **Não existe `main`.** O repositório estava vazio; só existe a branch de trabalho `ccr-8c6efdbd-nu48u7`. Sem `main` não há PR de merge
   nem proteção de branch. Criar `main` (por exemplo, apontando para o commit-base `a47994e`) e abrir o PR é decisão sua.
2. Executar `scripts/setup-github.sh Josperdias/TalentFlow` (proteção de `main`, revisão obrigatória de code owner, checks obrigatórios,
   merge squash, auto-merge). **Não foi executado**: exige a GitHub CLI autenticada como dono.
3. Informar o domínio do site (`PUBLIC_WEB_URL`) e o endereço da API.
4. Fornecer, por **GitHub Secrets** (nunca pelo chat): keystore do Android e, se quiser, certificado de assinatura do Windows.
5. Autorizar a publicação da Release (ela é gerada como rascunho).

## Segurança: avaliar antes de dados reais
Não houve auditoria independente, teste de intrusão, revisão de ameaças nem RLS. Há rate limit, CSRF, `Origin`, cabeçalhos, hash de senha
PBKDF2, tokens com rotação/detecção de reuso, escopo por empresa testado e produção que exige PostgreSQL + `COOKIE_SECURE`. Isso reduz risco
mas **não** equivale a "seguro para produção".
