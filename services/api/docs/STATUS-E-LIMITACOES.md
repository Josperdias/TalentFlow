# Status de engenharia e critérios de aceite — 2026-10-11

## Implementado e conferido por testes automatizados

- Inicialização do servidor FastAPI e healthcheck API HTTP 200.
- Login, logout, sessão, credenciais incorretas, controle RBAC por papel.
- 10 vagas, 120 candidatos, 2 tenants e dashboard de indicadores consultando banco.
- Criação/edição/duplicação de vagas, etapas, perfis e candidaturas.
- Pipeline Kanban com movimentação persistida e auditoria, revisão humana do fit.
- Entrevista criada/confirmada e scorecard ponderado persistido.
- Comunicação mock persistida; proposta criada/enviada, link e aceite único.
- Fluxo completo testado até contratado.
- Página pública de oportunidades e candidatura com consentimento obrigatório.
- Automações/tarefas parcialmente funcionais; testes criados/salvos.
- Upload DOCX, extração de texto, armazenamento e download protegido por papel/tenant; formatos PDF e DOC possuem implementações mas não tiveram testes automatizados aqui.
- Aprovação simples de vaga; anonimização/exclusão lógica de candidato.
- Teste básico de impedimento de leitura entre Nexa e Orbe.
- Portal de candidato privado por e-mail e tenant: etapas, entrevistas e propostas associadas ao seu login, validado em teste.

**Resultado de `pytest`: 8 testes de integração aprovados em execução local.** Esses testes **não** significam que todos os requisitos de aceite do escopo integral foram cumpridos.

## Verificação de interface

A página de login teve renderização em imagem local (`docs/login.png`), mas a execução do navegador automatizado completo para acessar e percorrer todos os fluxos foi bloqueada/restrita pelo ambiente. Portanto, **não há aprovação end-to-end de interação em navegadores reais, mobile físico ou auditoria WCAG**. Execução API de ponta a ponta foi testada por HTTP via TestClient.

## Funcionalidades incompletas — não confundir com produção

1. **Tecnologia:** não implementa React, Next.js ou Prisma; usa Vanilla JS + FastAPI/Python + SQLAlchemy e SQLite local, com possibilidade de configurar PostgreSQL. Nenhuma hospedagem SaaS foi publicada.
2. **Portal candidato:** dashboard autenticado permite ver as candidaturas próprias, suas etapas, entrevistas e propostas; **ainda não** permite executar testes nem confirmar entrevistas nem editar cadastro pelo login do candidato.
3. **Vagas:** cadastro cobre parte dos campos; requisição tem aprovação simples; não há fluxo completo em dois níveis, nem formulários, campos dinâmicos e perguntas eliminatórias configuráveis por vaga.
4. **Kanban:** drag-and-drop usa API nativa HTML5 desktop; falta suporte avançado a teclado, alternativa touch, seleção múltipla, ações em massa e automações complexas.
5. **Entrevistas:** agenda em lista e status funcionam; faltam calendário dia/semana/mês, confirmação pública, kit/roteiro de perguntas e sincronização Google/Microsoft.
6. **Testes:** definição e armazenamento de testes implementados; falta execução cronometrada pelo candidato, correção segura e visualização comparativa.
7. **Scorecard:** notas/pesos salvos por candidatura; falta construtor de templates versionados, comparação entre candidatos e obrigatoriedade granular.
8. **IA:** apenas heurística local revisável; sem LLM externo e sem interpretação robusta de consultas em linguagem natural. Parsing textual inicial, sem entendimento avançado estruturado de experiências e formação.
9. **Integrações:** e-mail/WhatsApp em modo mock, sem envio; calendário/link de videoconferência sem integração real; armazenamento local privado sem S3.
10. **Automação:** gatilho simples de mudança de etapa; falta agenda de execução para SLA/lembretes, condições encadeadas, retries e construtor visual com fluxos arbitrários.
11. **Analytics:** métricas e CSV disponíveis, mas faltam filtros cruzados extensivos, todos os relatórios detalhados, exportação Excel nativa e impressão refinada.
12. **LGPD e segurança:** papéis, cookies HttpOnly e isolamento básico incluídos; faltam revisão de ameaças, rate limiting, MFA, RLS DB, retenção automatizada, CSRF token explícito, segregação de armazenamento e auditoria externa.
13. **Qualidade:** não há validação manual de acessibilidade/responsividade em todos os tamanhos nem testes e2e de UI. Ainda podem existir fluxos visuais que precisem ajuste.

## Status frente ao escopo original

**Entrega atual: pré-MVP funcional local. Não é ATS completo e não satisfaz o critério de conclusão da missão integral.** Usar o pacote como base de desenvolvimento colaborativo real, evoluindo em incrementos testáveis.

## Próximo milestone de aceite

Adicionar migração PostgreSQL + migrações Alembic, suíte de permissões por endpoint, entrega de CRUD completo da vaga, interface móvel de Kanban, portal candidato privado, upload público do currículo, teste candidato e calendário integrado. Em seguida validar E2E real com Playwright e revisão de segurança antes de qualquer hospedagem pública.

## v0.4 — ampliação TalentFlow People
Novos módulos documentados em `STATUS-PEOPLE-v0.4.md` e `PESQUISA-PEOPLE-ANALYTICS-2026.md`. Testes de integração ampliados para 10 casos, incluindo autorização cross-tenant. Navegador automatizado bloqueado neste ambiente; UI não foi validada visualmente. Na versão local, a gestão de funcionários é demonstrativa e ainda não atende requisitos integrais de produção e LGPD.
