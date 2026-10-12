# Relatório verificável — TalentFlow People v0.4
- Data: 11/10/2026 (fuso Brasília) / 12/10/2026 UTC.
- Stack real: FastAPI/Python + SQLAlchemy SQLite local, frontend ES2022; PostgreSQL é meta de implantação, não foi testado nesta atualização.
- Funcionalidades novas: CRUD parcial Employee, transição do ATS com oferta aceita e etapa de contratado, onboarding, curso/inscrição, meta/progresso, review ponderado, evento de carreira, desligamento, novos painéis.
- Seis KPIs descritivos de dados persistentes, com numerador/denominador/metodologia.
- Base simulada: 24 funcionários (22 ativos + 2 desligados), 96 checklists, 6 cursos, 48 atribuições e 24 metas adicionais aos dados anteriores; valores gerados pela semente, não evidência real.
- Testes: `python -m pytest -q` (10 aprovados na verificação local), `node --check web/app.js` OK. Testes de navegador/móvel e segurança completos ainda pendentes.
- Correções e lacunas: adequar relação User↔Employee, ciclo completo de performance e LGPD, comparar períodos/coortes, exportação, análise de causas, UI mobile, migração versionada, testes de instalação em Postgres e serviço real de IA/integrações.
- Navegador de testes: tentativa de Playwright + Chromium na porta 8765 bloqueada com `net::ERR_BLOCKED_BY_ADMINISTRATOR`; screenshots de novas telas **não gerados**; a execução da API foi validada pelo TestClient, não pela navegação visual.
