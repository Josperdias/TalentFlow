# TalentFlow ATS — aplicação funcional (pré-MVP v0.3)

TalentFlow ATS é uma aplicação de recrutamento e seleção autoral, em português, com interface web responsiva, API HTTP, banco SQL persistente, autenticação, papéis, isolamento por empresa e base fictícia da **Nexa Tecnologia**. Não é uma página promocional nem apenas um protótipo visual: os fluxos implementados enviam dados reais à API e são persistidos no banco.

> **Estado:** versão local de desenvolvimento e demonstração, **não pronta para uso com dados pessoais reais nem para implantação pública sem revisão de segurança, acessibilidade e operação**. Leia `docs/STATUS-E-LIMITACOES.md` antes de expor a Internet.

## Como executar (Python 3.11+)

```bash
cd talentflow_ats
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000`. O banco SQLite `talentflow.db` incluído no pacote já contém os dados demonstrativos. Se ele for removido, é recriado e semeado automaticamente na primeira inicialização. A documentação interativa da API está em `/api/docs`.

**Credenciais fictícias (todos usam a senha `Demo@2026!`):**

| Papel | E-mail |
|---|---|
| Admin Nexa | `admin@nexa.demo` |
| Recrutamento Nexa | `recrutador@nexa.demo` |
| Gestor Nexa | `gestor@nexa.demo` |
| Entrevistador Nexa | `entrevistador@nexa.demo` |
| Candidato Nexa | `candidato@nexa.demo` |
| Admin outra empresa, isolamento | `admin@orbe.demo` |

**Importante:** nunca use esses usuários e senhas em um serviço público. O botão de login tem dados demonstrativos, apenas para desenvolvimento.

## Testes

```bash
pip install pytest httpx python-docx pymupdf
python -m pytest -q
```

Os testes de integração cobrem: login/sessão, dados iniciais, criação de vaga e candidato, candidatura, duplicidade, movimentação e audit trail, fit automático e revisão manual, entrevista, scorecard ponderado, comunicação mock, oferta com aceite público, acompanhamento privado do candidato, contratação, consentimento LGPD, isolamento entre tenants, papéis, automações/tarefas, upload DOCX e download protegido, aprovação de vaga e anonimização. A execução mais recente consta de `docs/STATUS-E-LIMITACOES.md`.

## Arquitetura implementada

- Web: JavaScript modular ES2022 sem build, HTML5 semântico, CSS responsivo; código em `web/`.
- API: FastAPI/Python com contratos JSON e validação Pydantic em `app/main.py`.
- Persistência: SQLAlchemy ORM com SQLite no pacote, configurável para PostgreSQL (`DATABASE_URL`) após instalação do driver `psycopg[binary]`.
- Login: cookies HttpOnly SameSite, sessão persistida em tabela com hash do token, 12 h, senhas com PBKDF2 salt individual; permissão por endpoint e escopo por empresa.
- Serviços: `app/adapters.py` com serviços locais para IA explicável, e-mail/WhatsApp em fila mock e armazenamento privado de currículos.
- Banco fictício: `app/seed.py` cria duas empresas independentes, Nexa com 10 vagas e 120 pessoas, estágios, entrevistas, scorecards, atividades e comunicações.
- Auditoria: histórico das mutações críticas em `AuditLog`.

A stack React/Next/TypeScript/Prisma solicitada **não foi implementada nesta entrega**. A ferramenta de hospedagem conectada falhou ao criar o projeto e o registro npm estava inacessível neste ambiente; por isso foi priorizado um produto realmente executável em vez de um frontend fictício. A API, o domínio e a camada de dados estão separados para permitir essa migração, sem alegar que ocorreu.

## Estrutura

```text
app/
  main.py          # API, validação, permissões e operações
  models.py        # Entidades e chaves SQLAlchemy
  database.py      # Engine SQL, sessões e inicialização
  seed.py          # Nexa/Orbe e dados fictícios determinísticos
  security.py      # Hash de senha e sessões
  adapters.py      # Serviços locais e contratos substituíveis
web/
  index.html       # Casca da aplicação
  styles.css       # Identidade visual e responsividade
  app.js           # Navegação e formulários conectados à API
tests/
  test_flow.py     # Testes de integração e autorização
docs/
  INVENTARIO-E-PRODUTO.md
  ARQUITETURA-E-COLABORACAO.md
  STATUS-E-LIMITACOES.md
CLAUDE.md           # Handoff para desenvolvimento colaborativo
requirements.txt
Dockerfile
docker-compose.yml
```

## Regras de dados

- Métricas do dashboard são consultas aos registros persistidos, não constantes visuais.
- Drag-and-drop envia mudanças à API, registra etapas e auditoria; transições críticas exigem motivo.
- A classificação automática de fit é **heurística e explicável**. Pode ser revisada pelo recrutador; não reprova ninguém autonomamente.
- O e-mail e o WhatsApp em modo mock **não são enviados a ninguém**. Eventos são registrados no banco.
- Dados de candidaturas da página pública são persistidos, com consentimento obrigatório.
- Dados da Nexa não podem ser consultados com sessão Orbe no escopo exercitado pelos testes. Uma auditoria de segurança independente ainda é necessária antes de produção.

## Compartilhamento com Claude

A pasta de handoff criada é: [Google Drive — TalentFlow ATS — Desenvolvimento colaborativo (ChatGPT + Claude)](https://drive.google.com/drive/folders/1bnWwYAN9hyFyw57DYP4SGvtdTJaV42q0).

Descompacte ou leia este ZIP e, para continuidade, comece por `CLAUDE.md`. O Claude **não está ligado automaticamente a esta conversa, ao Drive ou ao código local**; é necessário dar-lhe acesso à mesma pasta via conta/conector. Sincronização de concorrência deve ocorrer via Git, branch/PR, ou pastas de versões, com revisão humana. Evite que dois agentes sobrescrevam o mesmo artefato. Consulte `docs/ARQUITETURA-E-COLABORACAO.md`.

## Extensão 2026-10-11 — TalentFlow People v0.4

Foi criado um segundo domínio de **ciclo de vida do colaborador**, mantendo o ATS anterior intacto. Os novos arquivos `app/lifecycle.py`, `app/lifecycle_seed.py`, as classes adicionais em `app/models.py` e as telas do `web/app.js` permitem:
- Converter candidatura em colaborador após contratação no pipeline E proposta aceita; gerar automaticamente cinco marcos de integração.
- Cadastrar colaboradores, tarefas e conclusão da integração, cursos, inscrições e conclusões, metas quantitativas com progresso, avaliações ponderadas, promoções/transferências e saídas.
- Acessar as rotas `/app/people`, `/app/onboarding`, `/app/learning`, `/app/performance` e `/app/people/:id`.
- Consultar `/api/lifecycle/analytics` com seis métricas descritivas e metodologia + dados de coortes reais no banco, filtrados por tenant e papel.
- Visualizar dados fictícios adicionais de 24 colaboradores da Nexa, sem exposição da Orbe.

**Pesquisa e definições:** `docs/PESQUISA-PEOPLE-ANALYTICS-2026.md` e `docs/CATALOGO-INDICADORES.json`.

**Limitações:** esta versão não substitui um HRIS/ERP de produção, nem oferece instrumentos psicométricos validados, folha de pagamento, LMS completo ou segurança auditada. O fluxo colaborador só é gerado após comando explícito `POST /api/lifecycle/from-application/{id}` (não automaticamente na movimentação do Kanban). Consulte as pendências documentadas.
