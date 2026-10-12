# Inventário do baseline v1.2 (feito antes de qualquer migração)

Origem: `TalentFlow-People-v1.2-Servidor-PostgreSQL.zip` (Google Drive), importado sem alterações no commit `a47994e`.

## Divergência central: dois modelos de dados que não se falam

| | **Modelo A: relacional** | **Modelo B: snapshot JSONB** |
|---|---|---|
| Código | `app/main.py`, `lifecycle.py`, `workforce.py`, `models.py` | `app/workspace.py` + `web/workspace.js` (UI v1.1) |
| Armazenamento | ~30 tabelas (`jobs`, `applications`, `employees`, `development_plans`, `leave_requests`…) | 1 linha por empresa em `workspace_snapshots.data` (JSONB, até 2 MB) |
| Acesso | 5 papéis (admin, recrutamento, gestor, entrevistador, candidato) com escopo por vaga/equipe | **somente administrador** |
| Concorrência | nenhuma (último a salvar vence) | versão otimista do blob inteiro |
| Auditoria | `audit_logs` por ação | uma linha genérica "workspace alterado" |
| Testes | 8 + 10 casos de API | 6 casos de API |

Os dois **não eram sincronizados**: criar uma vaga na interface v1.1 (B) não aparecia na API relacional (A) e vice-versa.

### Decisão (ADR 0001)
A fonte única passa a ser o **modelo relacional (A)**: já tem RBAC, tenant, auditoria e testes. O snapshot (B) fica como legado
(somente administrador, desligado em produção) e como **fonte de importação**. Ver `docs/adr/0001-fonte-unica-relacional.md`.

## Módulos da v1.1 e onde estão hoje

| Módulo | Relacional (A) | No snapshot (B) | Estado na v1.3 |
|---|---|---|---|
| Vagas, aprovação, candidaturas, pipeline | sim | sim | **migrado**: web, Android, Windows |
| Banco de talentos, candidatos, currículos | sim | sim | **migrado** (lista/busca; upload só na API) |
| Entrevistas, scorecards, propostas | sim | sim | API v1 completa; **UI parcial** (ver STATUS) |
| Colaboradores, onboarding | sim | sim | **migrado** (lista); onboarding só na API |
| PDI e treinamentos | sim | sim | **migrado**: PDI nos 3 clientes |
| Férias e ausências | sim | sim | **migrado** (lista/decisão; criação no site) |
| Competências, GAP, evidências por cargo | **não existe** | sim | **pendente** (precisa de tabelas novas + importador) |
| Ciclos 90/180/360, calibração, 1:1 | **não existe** | sim | **pendente** |
| Mobilidade e sucessão | **não existe** | sim | **pendente** |
| Questionários/mapas comportamentais | **não existe** | sim | **pendente** (e sem diagnóstico automático) |
| Governança, decisões, qualidade de dados | parcial (`audit_logs`) | sim | **pendente** |
| People Analytics (catálogo, drill-down, coortes) | métricas básicas | sim | **parcial**: boletim e funil reais; sem coortes/drill-down |

## Lacunas de segurança e arquitetura encontradas (e o que foi feito)

| # | Lacuna | Ação na v1.3 |
|---|---|---|
| 1 | Só autenticação por cookie (sem cliente nativo) | tokens de acesso curtos + refresh rotativo com detecção de reuso |
| 2 | Sem controle de concorrência no modelo A | `version` + `If-Match` (428/409) em vaga, candidatura e PDI |
| 3 | Código da vaga `max(id)+1` colidia sob concorrência (500) | código derivado do id gerado pelo banco; teste com 12 threads |
| 4 | `create_all()` em produção, sem migrações | Alembic (`0001` = schema v1.2, `0002` = v1); produção recusa subir sem migrar |
| 5 | Teste "em PostgreSQL" nunca rodou em PostgreSQL (o `conftest` forçava SQLite) | `conftest` respeita `TF_TEST_DATABASE_URL`; CI roda em PG 16 |
| 6 | API servia a UI legada e `/workspace` em produção | desligados em produção |
| 7 | Origem exigia `Host` idêntico (quebra atrás de proxy) | `TRUSTED_ORIGINS` + guia de proxy |
| 8 | Sem feed de mudanças | `/api/v1/changes` (sem vazar ids a papéis restritos; negado a candidatos) |
| 9 | `/api/public/jobs` lista vagas de **todas** as empresas | **não corrigido**: ver STATUS (decisão de produto) |
| 10 | Sem RLS no PostgreSQL | **não implementado** (isolamento só na aplicação, coberto por testes) |
| 11 | Sem MFA, retenção automática, LGPD de titulares | **não implementado** |
| 12 | Rate limit em tabela do próprio banco | mantido; limite por IP configurável (`TF_LOGIN_IP_LIMIT`) |

## Rotas

83 rotas `/api/*` (main 52, lifecycle 19, workforce 7, workspace 4, auth 5). Na v1.3 as rotas de negócio foram expostas em
`/api/v1/*` (mesmas regras e RBAC) com OpenAPI em `packages/contracts/openapi.json` (70 caminhos). As rotas legadas continuam
funcionando em desenvolvimento, fora do OpenAPI.
