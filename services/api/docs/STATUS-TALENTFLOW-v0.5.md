# TalentFlow People v0.5 — release auditável
Data: 12/10/2026

## Progresso verificado
- 15 testes automatizados aprovados: 10 de ATS/People v0.4, 5 de controles de segurança e workflows v0.5.
- `node --check web/app.js` passou, Python compileall passou.
- API FastAPI inicializa localmente, responde health, aplicações e auditoria em testes HTTP.
- A interface tem rotas autenticadas para PDI, ausências/férias, People Analytics e segurança de sessões; formulários, ações e estados persistidos no banco.
- Preview visual automatizado **NÃO foi aprovado**: navegador Playwright/Chromium bloqueado por `net::ERR_BLOCKED_BY_ADMINISTRATOR` ao visitar localhost. Exigir QA manual desktop/mobile.

## Funcionalidades novas
- PDI (`DevelopmentPlan`): CRUD parcial (criação, consulta, arquivamento), checklist de ações, evidência, prazo, status e progresso calculado com revisão/auditoria. O ciclo permanece manual; avaliação psicométrica de competência não foi criada.
- Solicitações de ausência (`LeaveRequest`): criar, listar, aprovar, recusar; impedir datas sobrepostas e decisões repetidas; segregar permissões por tenant e gestor. Dias corridos, **não** saldo de férias, folha, cumprimento de CLT ou jornada.
- People Analytics: indicadores de headcount ativo, planos concluídos, pedidos pendentes, relatório com numerador/denominador e limitação metodológica; supressão de departamento com menos de 5 pessoas. Não se trata de análise preditiva ou validação científica de pessoas.
- Segurança: CSRF por sessão, validação Origin/Referer/Sec-Fetch-Site, tabela persistente de rate limiting, sessões revogáveis, CSP restringindo scripts a mesma origem, cabeçalhos defensivos, cookies Secure obrigatórios em produção, produção limitada a PostgreSQL e seed demonstrativo bloqueado.
- Currículos: assinatura inicial PDF/DOC/DOCX, verificação de estrutura DOCX, limites de tamanho e descompressão; parser anterior preservado.
- UX/UI: novos cards e painéis, seções e estados vazios, guias de leitura dos indicadores, foco visível, botão de pular para conteúdo, modal fecha por Escape e aprisiona Tab, Kanban abre card por Enter/Espaço, modo reduzido de animação, navegação móvel com sidebar rolável.

## Correções estruturais
- `tests/conftest.py` garante banco isolado em testes (evita alteração acidental no SQLite da demonstração durante import de módulos).
- `requirements.txt` inclui PyMuPDF e python-docx; Dockerfile inclui utilitário antiword para leitura de DOC legado.
- `scripts/bootstrap_admin.py` oferece criação interativa da primeira empresa/administrador, sem senha estática no código.
- `docs/REFERENCIAS-GITHUB-v0.5.md` registra quais repositórios foram pesquisados e quais padrões foram inspiradores; código GPL/AGPL de terceiros NÃO foi incorporado.

## Execução
Local: `python -m pip install -r requirements.txt && uvicorn app.main:app --host 127.0.0.1 --port 8000`
Testes: `python -m pytest -q`
Ativar produção: `APP_ENV=production`, `COOKIE_SECURE=true`, `DATABASE_URL` PostgreSQL de ambiente não-demo; provisionar empresa sem senha padrão via script. Isto são salvaguardas iniciais, não homologação.

## Bloqueadores de produção / próximos passos prioritários
1. Substituir `Base.metadata.create_all` por migrações Alembic testadas, prover backup/restauração e monitoramento.
2. MFA/SSO; recuperação de senha, auditoria de acesso a dados sensíveis, RBAC granular por política/área/gestor, tenant constraints compostas e testagem concorrente.
3. Redução de coleta e retenção de dados, DPIA/LGPD, criptografia de objetos e varredura antivírus de uploads. Revisar feedback sobre documentos médicos: atualmente texto livre é permitido; solicitar apenas metadados mínimos.
4. Auditoria independente de API, revisão do abuso de tokens públicos de proposta, reforço de rate-limit edge e monitoramento.
5. QA visual end-to-end em Chrome/Firefox e Android/iOS; testes automatizados de acessibilidade e testes de navegação.
6. Refatorar frontend vanilla monolítico para componentes reutilizáveis React/TypeScript, mantendo APIs estáveis.
7. Configurar métricas e instrumentos validados com população, amostragem, governança, finalidade e revisão de vieses antes de decisões de RH.
8. Folha, saldo de férias/feriados, ponto, contratos e benefícios permanecem adaptadores/módulos futuros.

## Licenças
Referências estudadas: Frappe HR (GPL-3), Horilla (ver licença do branch), shadcn/ui (MIT), Tabler Icons (MIT), OWASP Cheat Sheets (CC BY-SA). Nenhum código ou ativo desses repositórios foi copiado para a v0.5. Evitar incorporar GPL/AGPL sem revisão jurídica e documentação de conformidade.
