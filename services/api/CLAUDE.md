# Orientações para continuar o TalentFlow People v1.2

Trabalhe sobre esta base, não recrie o projeto. Produto: TalentFlow People, HCM/ATS com interface autoral v1.1, referências abertas como Frappe HR utilizadas apenas para padrões e arquitetura. O arquivo original offline está em `reference/TalentFlow-People-v1.1.html`; a versão conectada está em `private_views/workspace.html` + `web/workspace.js`, gerada por `scripts/prepare_workspace.py`.

API: `app/main.py` (legacy v0.5), `app/workspace.py` (estado v1.1 central, admin-only, tenant-scope, optimistic locking), `app/models.py`, `app/security.py`, `app/hardening.py`. PostgreSQL via Docker Compose; JSONB para snapshot. A carga demo vem de `private_demo_seed.json` e está bloqueada se `APP_ENV=production`.

IMPORTANTE: o modelo do estado JSONB não está sincronizado com a base relacional da API anterior. NÃO afirme que está. Preserve versionamento e isolamento por empresa. Prioridade: endpoints normalizados para vagas/candidatos/colaboradores/competências/ciclos, RBAC por entidade, migrações e auditoria por campo, seguida de troca gradual das chamadas do frontend.

Verificações: `python -m pytest -q` (18 testes), `node --check web/workspace.js`, `python scripts/browser_smoke.py` (transporte simulado). PostgreSQL Docker e end-to-end real não foram exercitados aqui. Nunca instalar ou compartilhar fontes proprietárias, nem tratar questionários exploratórios como avaliações psicológicas válidas. Não armazenar segredos em código ou Google Drive.

A cada alteração: revisar README-v1.2.md, escrever testes de isolamento, autorização e conflito, manter screenshots responsivos, e criar relatório preciso do que é real, mock ou pendente.
