# Referências públicas e decisões de implementação — v0.5

Consulta de 12/10/2026. Foram estudadas funcionalidades, padrões de composição e documentação — **nenhum código de projetos GPL/AGPL foi copiado**.

| Projeto | Repositório | Licença / observação | Padrão aproveitado | Aplicação original |
|---|---|---|---|---|
| Frappe HR | https://github.com/frappe/hrms | GPL-3.0 | Eventos de ciclo de vida, ausências, treinamento e competências | Models próprios LeaveRequest / DevelopmentPlan |
| Horilla HRMS | https://github.com/horilla/horilla-hr | Consultar licença por versão | Fluxo de integração, registros e aprovações de RH | CRUD e workflow de férias/ausências, PDI com evidências |
| shadcn/ui | https://github.com/shadcn-ui/ui | MIT | Hierarquia da interface, componentes acessíveis, dados com estados | Formulários e painéis do próprio TalentFlow, sem importar os componentes React |
| Tabler Icons | https://github.com/tabler/tabler-icons | MIT | Consistência de iconografia | Ícones atuais continuam próprios; arquivos Tabler não foram incorporados porque o ambiente não tem acesso de download ao raw GitHub |
| OWASP Cheat Sheet Series | https://github.com/OWASP/CheatSheetSeries | CC BY-SA 4.0 docs | Autenticação, limitação de tentativas, CSRF | Rate limit persistente, cabeçalhos e token por sessão |

## Segurança implementada

1. Sessão aleatória em cookie HttpOnly, Secure obrigatório em APP_ENV=production; digest armazenado no banco.
2. Proteção CSRF com token derivado da sessão, entregue por endpoint autenticado, exigido no cabeçalho para mutações de usuário logado.
3. Verificação de Origin, Referer e Sec-Fetch-Site para mutações; sem CORS permissivo.
4. Rate limits persistentes para login, candidatura e resposta de proposta (chaves hash); reforçar com proxy de borda em produção.
5. CSP com script-src self; não permite inline JS, mantendo inline style apenas no legado; X-Content-Type-Options, HSTS em HTTPS, Permissions-Policy e Cache-Control: no-store em endpoints.
6. Recursos de sessão para listar e revogar sessões antigas.
7. Dados fictícios desativados automaticamente com APP_ENV=production. Ainda exige provisionamento externo de usuários, deploy HTTPS e migrações de banco.
8. Férias/ausências e PDI isolados por tenant, com validação de referências, ações auditadas e checagem de gestor responsável.

## Limitações e ameaças restantes

- Não substitui pentest, SAST/DAST, revisão LGPD/DPO e migrações Alembic.
- SQLite local, FastAPI e frontend vanilla; não é a stack React/Next preferida originalmente.
- Rate limit persistente depende de DB compartilhado, sofre concorrência entre transações em volume muito alto. Complementar no edge em produção.
- Ausências/férias registram pedidos de datas corridas, **não** fazem cálculo de saldo de férias, folha, feriados, convenções coletivas ou regras CLT.
- Componente de calendário, questionários, payroll, MFA/passkeys e SSO ainda pendentes.
- Índices de engajamento, risco de turnover e escore de potencial NÃO são calculados sem validação do instrumento, amostragem ou governança.
- Tabler e shadcn/ui são referências de design, não dependências incluídas. Reuso exigiria port React e controle de licença.
