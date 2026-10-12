# Arquitetura

```text
Android (Kotlin/Compose) ──┐
Windows (C#/WinUI 3) ──────┼──> HTTPS ──> API FastAPI /api/v1 ──> PostgreSQL 16
Site (React/TS, ZIP) ──────┘                │   RBAC + escopo por empresa + auditoria no servidor
                                            └─> arquivos privados (currículos)
```

Os três clientes **nunca** falam com o banco. Regras de negócio e permissões vivem no servidor; esconder um botão nunca é a proteção.

## Monorepo

| Pasta | Conteúdo |
|---|---|
| `services/api/` | FastAPI, modelos SQLAlchemy, **Alembic**, testes (pytest), Dockerfile. Contém também a UI legada v1.1 (só desenvolvimento). |
| `apps/web/` | React + TypeScript + Vite; `deploy/` (guia, Nginx, Apache); `e2e/` (Playwright/Chromium). |
| `apps/android/` | `:core` (Kotlin puro, testável em JVM) e `:app` (Compose). |
| `apps/windows/` | `TalentFlow.Core` (net8.0) + testes, `TalentFlow.Windows` (WinUI 3), `installer/` (Inno Setup). |
| `packages/design-tokens/` | `tokens.json` -> CSS, Kotlin e XAML/C# (gerados, com verificação de deriva no CI). |
| `packages/contracts/` | `openapi.json` exportado da API (verificado no CI). |
| `infra/` | `docker-compose.yml`, `.env.example`, `backup.sh`, `restore.sh`. |
| `scripts/` | empacotar o site, E2E, políticas, configuração do GitHub, PostgreSQL de desenvolvimento. |
| `.github/workflows/` | `ci`, `android`, `windows`, `release`, `auto-merge`. |

## Autenticação

| Cliente | Mecanismo | Onde fica o segredo |
|---|---|---|
| Site, mesma origem (recomendado) | cookie `HttpOnly` + `SameSite=Lax` + token CSRF por sessão | cookie (JS não lê) |
| Site, API em outro domínio | Bearer (access em memória, refresh em `sessionStorage`) + `CORS_ORIGINS` | memória / sessionStorage |
| Android | Bearer; access 15 min + refresh rotativo | **Android Keystore** (AES-256-GCM) |
| Windows | Bearer; mesmo esquema | **DPAPI** (usuário atual) |

Refresh token de uso único; reapresentar um token já usado derruba toda a família de sessões (suspeita de roubo).
Cookie de navegador e token de API **não são intercambiáveis** (testado). Limites de tentativa por conta e por IP.

## Sincronização entre clientes

1. Toda escrita grava `audit_logs` na mesma transação.
2. `GET /api/v1/changes?after=<cursor>` devolve **quais entidades mudaram**, sem `before/after`; `entity_id` só para administração
   e recrutamento; negado a candidatos.
3. Cada cliente consulta a cada ~4-5 s (apenas com a janela visível), e **rebusca pelos endpoints normais** (que aplicam RBAC).
4. Edições usam `If-Match: <version>`. Servidor responde **428** se faltar e **409** (com a versão atual) se outro cliente salvou
   antes. Os três clientes mostram o diálogo de conflito e nunca sobrescrevem em silêncio; o formulário de edição fica preso à
   versão em que foi aberto, mesmo se a tela ao fundo atualizar.
5. Sem rede: o cliente mostra "Sem conexão" e mantém o que já exibia marcado como desatualizado. **Não há modo offline simulado.**

Limite atual: polling, não SSE/WebSocket (latência de segundos).

## Dados e migrações

Alembic: `0001` reproduz exatamente o schema v1.2; `0002` adiciona `refresh_tokens`, metadados de sessão e `version`
(jobs, applications, development_plans). Validado: subir, `alembic check` (sem deriva), descer, subir; upgrade de um banco v1.2 **com dados**.
Em produção a API **recusa subir** sem migrações aplicadas.

## Segurança resumida

Senhas PBKDF2-SHA256 (240 mil iterações); sessões só com hash no banco; CSRF em cookie; verificação de `Origin` com
`TRUSTED_ORIGINS`; rate limit; cabeçalhos de segurança; CSP estrita no site (sem scripts de terceiros, fontes empacotadas);
produção exige PostgreSQL, `COOKIE_SECURE=true`, sem dados de demonstração. Ver limitações em `STATUS.md`.
