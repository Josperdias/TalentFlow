# Registro de testes (números reais, com ambiente)

Convenção: "local" = container de desenvolvimento (Ubuntu 24.04, Python 3.13, Node 22, JDK 21, .NET 8.0.131, PostgreSQL 16.15 sem Docker).
"CI" = GitHub Actions (`ubuntu-latest`, `windows-latest`, PostgreSQL 16 em contêiner de serviço).

## 1. API (`services/api/tests`)
| Suíte | Casos | Resultado |
|---|---|---|
| Herdada da v1.2 (fluxo ATS, People, endurecimento, workspace) | 18 | passam em PostgreSQL 16 real (local e CI) e SQLite |
| `test_v1_native.py` (novos) | 18 | passam (total 36) |

Cobertura dos novos casos: login por token; senha errada e cliente desconhecido; cookie x Bearer **não intercambiáveis**; refresh
rotativo e **detecção de reuso** (derruba a família); logout revoga o dispositivo; listar/revogar sessões; **isolamento entre empresas**
via Bearer (404 em leitura e PATCH); RBAC (candidato 403, gestor não cria vaga); `If-Match` obrigatório (428) e **conflito 409 entre dois
clientes** em vaga, candidatura e PDI; feed `/changes` propaga entre clientes, **oculta ids a papéis restritos** e é negado a candidatos;
código de vaga único com 12 criações concorrentes; limite de tentativas por conta ainda vale; OpenAPI só expõe `/api/v1`;
página de carreiras **por empresa**.

Detalhe importante: a v1.2 relatou "18 testes aprovados" com SQLite, mas o `conftest.py` **forçava SQLite**, então a suíte nunca tocou
PostgreSQL. Foi corrigido (`TF_TEST_DATABASE_URL`) e a execução em PostgreSQL foi confirmada por contagem de linhas
(32 tabelas, dados semeados).

## 2. Migrações Alembic
`0001` (schema exato da v1.2, gerado dos modelos do commit-base) e `0002` (v1). Verificado: `upgrade head`, `alembic check`
("No new upgrade operations detected"), `downgrade base`, `upgrade head`; **upgrade de um banco v1.2 com dados** (vaga antiga ficou com
`version=1`, sessão com `kind=cookie`) e downgrade preservando as linhas. Repetido no CI.

## 3. Produção (local)
`APP_ENV=production`: recusa subir sem migrações; com migrações e `provision_admin`: `/` e `/workspace` e `/api/workspace/*` -> 404;
conta de demonstração -> 401; login do administrador criado -> token; lista de vagas vazia; cabeçalhos de segurança presentes.

## 4. Site
| Teste | Resultado |
|---|---|
| `tsc --noEmit` + `vitest` | 5 testes passam |
| E2E em Chromium (`apps/web/e2e/e2e_web.py`) | **16/16** |
| mesmo E2E sobre o **ZIP descompactado** | 16/16 |
| mesmo E2E no CI (ZIP, PG de serviço) | ver workflow `ci` |

Passos do E2E: diagnóstico da API; senha errada; login + visão geral com dados reais; sessão após recarregar (cookie `HttpOnly` ilegível por JS);
lista de vagas; **mover candidatura persiste no servidor** (verificado por outro cliente); **mudança feita por outro cliente aparece sem
recarregar**; **conflito: o formulário avisa durante a edição e salvar não sobrescreve**; PDI com evidência persistida; ausência registrada e
aprovada; sessões/logout; sem erros de JS; gestor (menu restrito); candidato (só portal); celular 390 px (navegação inferior, sem rolagem
horizontal); servidor inalcançável (aviso, sem dado falso). Rodado com **CSP estrita**, em banco **novo** criado por Alembic.

Falhas encontradas e corrigidas ao longo do caminho (não esconder): proxy reescrevendo `Host` bloqueava o login; o formulário de edição
"rebaseava" na versão nova quando outro cliente salvava durante a edição (risco de sobrescrita silenciosa); o E2E dependia de banco
acumulado; cinco pares de cor reprovavam no contraste WCAG.

## 5. Kotlin (`apps/android/core`)
13 unitários (servidor simulado: login, refresh, reuso, `If-Match`/409, rede, feed, URL, versões) + 3 de **integração contra a API real**
(isolamento entre empresas; A cria -> B vê pelo feed -> conflito 409; refresh real rotaciona). Local (JVM 21, `release 17`) e CI (JDK 17).
O CI confere que a integração **não foi pulada** (`skipped == 0`).

## 6. C# (`apps/windows/TalentFlow.Core.Tests`)
20 casos unitários (incluindo `Theory`) + 3 de **integração contra a API real** (mesmos cenários). Local (.NET 8) e CI (ubuntu).

## 7. Clientes nativos na interface
- **Android (CI):** APK de depuração compila e é verificado com `aapt2` (sem WebView). O teste instrumentado Compose
  (`LoginAndSyncTest`: servidor -> login -> visão geral -> criar vaga pela UI -> vaga criada por **outro cliente** aparece sem recarregar)
  roda em emulador API 34 contra a API real; **status: ver `STATUS.md`** (estava falhando com timeout de espera; diagnóstico em andamento).
- **Windows (CI):** publicação, instalador e zip gerados; teste de fumaça abre o app e captura a tela. Sem teste manual.
- **Compose (CI):** subir, provisionar admin, login, backup, apagar dados, restaurar: verde.

## 8. Não testado
Docker Compose no ambiente local (o CI tem o job), Nginx/Apache reais, subpasta real, leitor de tela, axe/Lighthouse, dark mode visual, carga/concorrência
alta, restauração de backup em servidor real, PostgreSQL em outra versão, navegadores além do Chromium, iOS/Safari.
