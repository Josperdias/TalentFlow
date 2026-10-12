# TalentFlow People v1.2 — aplicação conectada

**Estado:** projeto executável para desenvolvimento local; **não homologado para produção com dados pessoais reais**.

Esta entrega mantém a interface v1.1 (ciclos, carreira, competências, seleção, governança e People Analytics) e acrescenta sincronização autenticada e persistência central no banco. Aproveita o backend FastAPI da v0.5, incluindo sua API existente para vagas, candidaturas, colaboradores e aprovações.

## Como executar com PostgreSQL (Docker)

1. Instale Docker Engine/ Docker Desktop com Compose.
2. Copie `.env.example` para `.env` e substitua `PGPASSWORD` por uma senha exclusiva e forte.
3. No diretório do projeto: `docker compose up --build -d`.
4. Abra **http://localhost:8000/login**. Em ambiente de demonstração, use `admin@nexa.demo` e a senha de desenvolvimento já documentada no projeto (`Demo@2026!`).
5. Depois do login, acesse **http://localhost:8000/workspace** para a versão v1.1 conectada. A interface anterior com endpoints relacionais permanece em `/app/dashboard`.
6. Para encerramento: `docker compose down` (**não** usar `-v`, pois isso apagaria o volume do banco).

O servidor utiliza PostgreSQL 16 e `psycopg` (JSONB para a coleção `workspace_snapshots`). A API e as páginas são servidas pela mesma origem; não há dependência de serviço externo de autenticação.

### Execução sem Docker (testes locais)

```bash
python -m venv .venv
# Ative a venv segundo seu sistema operacional.
pip install -r requirements.txt
# Somente para testes, na pasta do projeto:
export DATABASE_URL=sqlite:///./talentflow-dev.db
export APP_ENV=development
export DEMO_SEED=true
export COOKIE_SECURE=false
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

No Windows PowerShell, defina as variáveis com `$env:DATABASE_URL=...` e equivalente para as demais.

## Onde ficam as funcionalidades

- `/login` — login do sistema já existente.
- `/workspace` — interface completa v1.1 conectada, **somente administradores**; carrega o estado pela API, bloqueia alterações sem sessão e utiliza gravação versionada.
- `/api/workspace/state` — GET/POST do estado central (admin, mesma empresa, proteção CSRF, limite de 2 MB).
- `/api/workspace/metrics` — contagens e taxas com numerador/denominador sobre o estado da empresa autenticada.
- `/api/workspace/status` — status da versão persistida.
- `/api/audit` — trilha de auditoria do servidor (separada do histórico visual local).
- `/app/dashboard` — interface original baseada em endpoints relacionais, com permissões conforme função e atribuições já implementadas.
- `/api/docs` — documentação dos endpoints FastAPI.

## Controles implementados

Sessões aleatórias no servidor com cookie `HttpOnly`, `SameSite=Lax` e `Secure` quando habilitado; CSRF vinculado à sessão; bloqueio de origem cruzada; limite de login; restrição de papéis; `company_id` extraído exclusivamente da sessão; `SELECT/UPDATE` condicionados à empresa; transação com versão otimista; conflito HTTP 409; eventos de auditoria em tabela protegida por autenticação; mensagens de erro/backup em caso de falha de sincronização.

O HTML público original em `reference/` continua **offline e demonstrativo**. Ele não herda esses controles quando aberto como arquivo individual. Não use dados pessoais reais nele.

## Como criar uma empresa sem credenciais fictícias

Em ambiente **isolado, configurado com banco real**:

```bash
APP_ENV=production DEMO_SEED=false DATABASE_URL='postgresql+psycopg://...' python -m scripts.provision_admin --company 'Minha Empresa' --slug minha-empresa --email admin@empresa.com
```

A senha é pedida no terminal de forma oculta, nunca gravada no código. A implantação de produção exige HTTPS, `COOKIE_SECURE=true`, banco separado e serviços de backup/monitoramento. O exemplo Docker é **apenas para desenvolvimento local**.

## Testes

```bash
python -m pytest -q
node --check web/workspace.js
node --check web/app.js
python scripts/browser_smoke.py
```

- **18 testes da API aprovados** com SQLite em banco isolado. Cobrem isolamento entre empresas, autenticação, operações de RH, CSRF e versionamento do workspace.
- **Teste de navegador controlado aprovado** em 1440 px e 390 px, incluindo criar vaga, observar gravação versionada e ausência de overflow horizontal. Para contornar bloqueio de navegação local do Chromium neste ambiente, o teste visual simula apenas o transporte HTTP. A API verdadeira foi testada separadamente.
- **PostgreSQL via Docker não foi executado nesta sessão**, por indisponibilidade do daemon. Os arquivos de provisionamento estão preparados, mas requerem teste no ambiente de destino.

## Limitações não ocultadas

1. **Migração intermediária:** a interface v1.1 persiste um documento JSONB por empresa, ainda sem normalização completa dos seus registros em tabelas individuais.
2. **Dois modelos coexistentes:** as APIs relacionais herdadas e o estado JSONB conectado não são automaticamente sincronizados entre si. Use um fluxo de cada vez, sem assumir que alterações de um aparecerão no outro.
3. **Permissões:** o `workspace` v1.1 inteiro está disponível apenas para `admin`; os outros papéis usam rotas próprias do backend antigo. Permissões por campo, equipe e ciclo na nova interface ainda não foram migradas.
4. **Concorrência:** conflito de gravação é detectado; o sistema não faz mesclagem automática de alterações. Em conflito, exporte as mudanças locais para revisão e recarregue a versão atual.
5. **Arquivos:** o armazenamento dos currículos no backend anterior ainda é local; faltam S3, criptografia em repouso gerenciada e políticas completas de retenção.
6. **LGPD:** falta DPIA/RIPD, fluxo institucional de titulares, retenção, anonimização transversal e análise de segurança independente.
7. **Frappe HR:** permanece referência de arquitetura e mapeamento, sem conexão ativa. Não copiamos o código GPL-3.0.
8. **Psicometria:** questionários comportamentais não validados, inadequados como critérios automáticos para contratação.
9. **Operação empresarial:** faltam monitoramento, testes de carga, gestão de segredos, MFA, e2e no Chrome real com API e testes com profissionais de RH.

**Próxima etapa de desenvolvimento:** migrar progressivamente as entidades centrais do JSONB para tabelas com `company_id`, chaves estrangeiras e endpoints com RBAC por recurso; manter o frontend e fazer com que o dashboard consuma exclusivamente essas APIs.
