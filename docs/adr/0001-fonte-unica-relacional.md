# ADR 0001: fonte única da verdade = modelo relacional

- Estado: aceito (2026-10-12)
- Contexto: a v1.2 tem dois modelos de dados desconectados (tabelas relacionais e snapshot JSONB). Três clientes
  (site, Android, Windows) precisam ler e escrever **os mesmos registros** com permissões por papel.
- Decisão: **tabelas relacionais** são a fonte canônica. O snapshot JSONB deixa de ser escrito por clientes novos; permanece como
  legado administrativo (desligado em produção) e como origem de importação idempotente dos módulos que ainda não têm tabelas.
- Por quê: o modelo relacional já tem escopo por empresa, RBAC por entidade, auditoria, constraints e testes; o snapshot só
  permite administrador e sobrescreve o blob inteiro (inviável com três clientes concorrentes).
- Consequências:
  - Módulos que existem só no snapshot (competências, ciclos, mobilidade, questionários, governança) exigem tabelas
    novas, migrações Alembic e um importador com relatório de reconciliação antes de aparecerem nos clientes nativos.
  - Sincronização entre clientes = leituras autorizadas + `If-Match` + feed `/changes`, não replicação de blob.
  - Evitar dupla escrita: cada entidade tem uma única fonte canônica por vez.
- Alternativas descartadas: manter JSONB como canônico (sem granularidade de permissão, conflito de blob inteiro);
  dupla escrita contínua (divergência silenciosa).
