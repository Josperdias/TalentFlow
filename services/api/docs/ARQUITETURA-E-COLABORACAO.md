# Fase 2 — Arquitetura, entidades, segurança e trabalho colaborativo

## Camadas atuais

`web/app.js` → `fetch('/api/...')` (cookies SameSite) → `app/main.py` (Pydantic, regras RBAC, autorização de recursos) → `app/models.py` (SQLAlchemy) → SQLite `talentflow.db` / PostgreSQL por DATABASE_URL.

`app/security.py`: validação de login + sessão persistida; `app/adapters.py`: classificação local de fit, templates/registro mock e arquivos privados; `app/seed.py`: dados fictícios. `app/main.py` mantém rotas extensas por restrições de tempo: separar em `routers/{auth,jobs,candidates,pipeline,...}.py` e `services/` na evolução.

Não foi possível provisionar o projeto externo de hospedagem solicitado. Em vez de alegar Next.js/PostgreSQL de produção, este pacote inclui serviço local testável. A migração para React/Next/TypeScript pode consumir a mesma API após versionar contratos (`openapi.json`) e alinhar proteção CSRF/CORS.

## Mapeamento de entidades implementadas

`Company` → `User` (`role`) e todos os modelos privados com `company_id`.
`User` → `Session` (hash SHA-256 do token) e `AuditLog`.
`Job` → `JobStage`, `Application`, `JobApproval`.
`Candidate` → `Application`, `Resume`, listas de talentos.
`Application` → `Interview`, `Scorecard`, `Activity`, `Communication`, `Offer`, `Task`.
`Automation` → `AutomationRun`; `TestDefinition` → `TestAttempt`.

Relacionamentos e chaves estão definidos nas classes `app/models.py` com os tipos reais utilizados. Não afirme que todas as 27 entidades detalhadas no escopo original existem separadamente (por exemplo, Education e Experience são campos resumidos de Candidate nesta versão).

## Modelo de acessos

- admin: CRUD, aprovações, anonimização e auditoria.
- recruiter: vagas, candidaturas, avaliações, entrevistas e comunicação.
- manager: somente vagas atribuídas, candidaturas dessas vagas; avaliação conforme endpoint.
- interviewer: somente candidaturas designadas via entrevistas; avaliação conforme endpoint.
- candidate: login e portal demonstrativo; candidatura pública disponível sem login.

Escopo de tenants é aplicado por `company_id` nas consultas e vínculos internos, com teste de isolamento Orbe vs Nexa. Recursos críticos são verificados quanto a atribuição. Em produção exigir suíte de autorização exaustiva em **cada endpoint**, revisão de consultas, observabilidade e RLS no PostgreSQL (atualmente ausente).

## Segurança antes de implantação real

- Remover seed automático e credenciais fixas de produção, instalar gerenciamento de contas/invites.
- `COOKIE_SECURE=true` atrás de HTTPS e configurar cookies por domínio correto, CSRF tokens, políticas CORS e proxies confiáveis.
- Rate-limit no login, cadastro público, endpoints de upload e oferta; reset de senha/MFA.
- Banco gerenciado PostgreSQL com migrações, backup, criptografia em repouso, isolamento de serviço e RLS como segunda barreira.
- Antivírus/validação MIME e tamanho de currículos, segregação de buckets/ACL, varredura de uploads.
- Consentimento em registro, prazo de retenção, exportação, anonimização com trilha e políticas para solicitações LGPD.
- Auditoria com retenção, logs seguros, monitoramento e revisão OWASP.
- Evitar dados sensíveis reais no Drive ou repositório. Neste material, dados são sintéticos.

## Convenção de colaboração com Claude

**Fonte de verdade:** Git (a ser iniciado em repositório privado pelo usuário), commit e PR; este Drive é um repositório de *artefatos e especificações* e não substitui merge. Sem Git, exigir arquivos versionados (v0.3, v0.4 etc.) e manifestos de diffs.

**Papéis sugeridos:** ChatGPT prioriza backend, integrações, testes e segurança; Claude foca UX, acessibilidade, design system e revisão cruzada, com escopos de arquivos separados. Pode mudar, desde que o mesmo arquivo não seja alterado por ambos sem PR.

**Fluxo:** (1) abrir `README.md`, `CLAUDE.md`, este arquivo e status; (2) baixar ZIP; (3) rodar testes; (4) criar branch `feat/...`; (5) alterar com testes; (6) escrever relatório de mudanças e pendências; (7) publicar artefato versionado no Drive/PR; (8) outro agente revisa.

**Pasta:** https://drive.google.com/drive/folders/1bnWwYAN9hyFyw57DYP4SGvtdTJaV42q0. O Claude precisará conectar-se ao mesmo Drive/receber acesso; não existe execução simultânea autônoma entre assistentes apenas por criar a pasta.
