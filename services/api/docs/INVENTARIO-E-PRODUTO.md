# TalentFlow ATS — Fase 1: engenharia reversa e inventário

## Origem das referências e nível de certeza

**Fontes consideradas:** pedido detalhado do proprietário; URL pública https://www.inhire.com.br/demo; páginas públicas de produto (por exemplo `/produto/selecao`). A URL da demo expõe uma apresentação incorporada, mas ela não disponibilizou, nesta execução, inspeção automatizada completa de todos os estados internos; **não se reivindica reprodução fiel de cada screenshot do InHire**. Prints específicos de ATS não estavam anexados nesta mensagem; o anexo presente estava nomeado Modo-Treino-Prompt-para-Claude.md e corresponde a outro produto, portanto foi deliberadamente ignorado para esta aplicação.

**Verificado em materiais públicos:** plataforma de vagas, pipeline Kanban, entrevistas, scorecards, triagem assistida, automações e painéis de RH. **Especificado pelo usuário:** demais módulos, entidades, papéis, campos e microinterações. **Decisões próprias de design:** layout, copy, sistema de cores e organização das interfaces.

## Inventário por tela

| Tela / rota | Usuários | Dados | Ações e fluxo | Estados e lacunas |
|---|---|---|---|---|
| Login `/login` | Todos | E-mail, senha, sessão | Entrar → dashboard / portal candidato | Erro de credenciais e estado carregando; recuperação de senha ainda ausente |
| Dashboard `/app/dashboard` | Admin, RH, gestores/entrevistadores autorizados | Vagas, candidaturas, entrevistas, scorecards | Ver KPIs, distribuição por etapa, origens e atividades → vaga/pessoas | Indicadores derivados do banco; filtros analíticos completos pendentes |
| Vagas `/app/jobs` | Admin, RH, gestores autorizados | Título, código, área, local, modalidade, status, responsável, contagem | Filtrar, abrir, criar, duplicar, editar, fechar/arquivar | CRUD parcial; editor de todos os campos/etapas pendente |
| Pipeline `/app/jobs/:id` | RH, gestores e entrevistadores designados | Etapas e candidaturas da vaga | Buscar, arrastar card, abrir candidato, mover com motivo | Desktop drag/drop real; UX móvel e seleção em massa incompletas |
| Banco de candidatos `/app/candidates` | Admin/RH; acesso restringido por atribuições para outros papéis | Nome, cargo, fonte, competências, cidade, experiência | Busca, abrir perfil, criar candidato | Tags e listas avançadas pendentes |
| Detalhes do candidato (drawer) | Admin/RH/atribuídos | Contatos, currículos, candidaturas, fit, entrevistas, scorecards, histórico, oferta | Registrar entrevista, avaliar, enviar mock, revisar fit, proposta | Abas de educação/experiências normalizadas e notas/anexos extra pendentes |
| Entrevistas `/app/interviews` | Entrevistadores designados / RH / gestor | Data, duração, entrevistador, status | Agendar, confirmar, consultar | Calendário dia/semana/mês e vídeo externo pendentes |
| Testes `/app/tests` | Admin/RH | Título, tempo, corte, questões | Construir teste de alternativa simples | Execução pelo candidato e timer pendentes |
| Automações `/app/automations` | Admin/RH | Gatilho, condição, ação, contagem | Criar regra, pausar/ativar, ver logs | Construtor simplificado; condições compostas pendentes |
| Propostas `/app/offers` | Admin/RH | Cargo, salário, validade, status, link de aceite | Criar, enviar mock, acessar aceite público | Aprovações multinível e PDF de oferta pendentes |
| Relatórios `/app/reports` | Admin/RH | Agregações do banco | Visualizar relatório, baixar CSV | Excel nativo e relatório customizado pendentes |
| Tarefas `/app/tasks` | RH/usuários designados | Atividades, prazo, estado | Concluir/reabrir tarefa | Alertas agendados e integração externa pendentes |
| Auditoria `/app/audit` | Admin | Ação, autor, entidade, antes/depois | Consultar rastreabilidade | Exportação e retenção personalizável pendentes |
| Página pública `/carreiras` | Visitantes / candidatos | Identidade Nexa e vagas abertas | Explorar vaga → candidatar-se | Personalização multiempresa pendente |
| Aplicação pública | Visitantes | Dados pessoais, currículo-texto, vaga, aceite LGPD | Enviar → registrar candidato/candidatura no banco | Upload público de arquivos e questionário configurável pendentes |
| Aceite de oferta `/oferta/:token` | Titular do link | Proposta, data, salário | Aceitar/recusar; estado terminal persistido | Fluxo interno posterior à assinatura/contratação é manual |
| Portal candidato autenticado | Candidato | Candidaturas vinculadas a seu e-mail, etapas, entrevistas e propostas | Consultar inscrições, seguir link de proposta e navegar para vagas | Testes online e confirmação de entrevista pelo portal pendentes |

## Modelo funcional: transições

- **Vaga:** aprovação → aberta → encerrada/arquivada; usuário com permissão edita/reabre por API, com trilha de auditoria. Aprovação simples implementada; workflow gestor/RH em múltiplas aprovações ainda não.
- **Candidatura:** `active` em etapa customizada; `hired`/`rejected` em etapas de destino. Movimentações registram autor, origem, destino e motivo quando destino é crítico.
- **Entrevista:** scheduled → confirmed/completed/cancelled/no_show; validações de data e conflitos podem ser aprofundadas.
- **Proposta:** draft → sent → accepted/declined. Aceite externo por token imprevisível, consumido apenas uma vez. Os demais estados solicitados ainda exigem implementação.
- **Comunicação:** fila mock persistida, **sem disparo externo**; status distingue claramente o modo de operação.
- **Automação:** regra `stage_changed`, opcionalmente filtrada por nome da etapa → evento registrado, comunicação mock; pode pausar/retomar.

## Decisões de UX

Sidebar escura com contexto da Nexa, canvas claro com tipografia densa, acento roxo, tabelas densas e cartões de candidatos, estados de carregamento/erro/confirmar via aplicação, tela de login editorial, responsividade para tela pequena. Marca/textos próprios de TalentFlow. Os módulos foram priorizados por fluxo, não por aparência estática.

## Backlog prioritário a validar com Claude

1. Completar portal candidato individual e granularidade por gestor/entrevistador.
2. Formularios por vaga e anexos públicos (armazenamento privado com assinatura), anti-spam/rate limiting.
3. Biblioteca de critérios de scorecard, kits estruturados, avaliação por etapa, teste do candidato.
4. Busca natural AIService, extração enriquecida e revisão humana, sem discriminação algorítmica.
5. Adaptadores de e-mail, WhatsApp, calendário e storage em produção.
6. PostgreSQL como padrão de implantação, migrações Alembic, filas assíncronas, rate limit e logs imutáveis.
7. Responsividade do Kanban (reordenação acessível por botões no mobile) e acessibilidade WCAG.
