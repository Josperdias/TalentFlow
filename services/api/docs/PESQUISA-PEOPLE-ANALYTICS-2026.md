# TalentFlow People — pesquisa de inovação e arquitetura de gestão do ciclo de vida
**Estado:** pesquisa de produtos e de literatura, 11/10/2026; implementação local v0.4 em andamento. Não representa certificação ISO, validação psicométrica ou parecer jurídico.

## Tese de produto
Deixar de tratar o ATS e o HRIS como ilhas: dados de candidato e candidatura originam, após aprovação + aceite + contratação formal, um registro distinto de colaborador. O colaborador mantém histórico de integração, competências, aprendizados, objetivos, feedbacks, movimentação, sucessão e desligamento. Aplicar gestão baseada em evidências, e não dashboards que atribuem causalidade a correlações.

## Benchmark de plataformas abertas — o que estudar, NÃO incorporar cegamente
| Referência | Funcionalidades observadas | Decisão TalentFlow | Atenção de licença |
|---|---|---|---|
| Frappe HR (https://github.com/frappe/hrms) | Ciclo do colaborador, onboarding, promoção/transferência, feedback, avaliação e folha | Entidade Employee separada de Candidate e eventos de carreira | GPLv3 no repositório; conferir componentes |
| Horilla HRMS (https://github.com/horilla/horilla-hr) | Recrutamento → onboarding/offboarding, ausências, frequência | Checklists por fase, concluídos por responsável, prazos e auditoria | Conferir arquivo LICENSE/versão |
| OrangeHRM Starter (https://github.com/orangehrm/orangehrm) | RH modular, experiência de autosserviço e operações | Diretório único e papéis/escopos; self-service planejado | GPLv3 |
| OCA HR (https://github.com/OCA/hr) | Cursos, contratos e appraisals como addons | Extensões independentes e APIs separadas por domínio | Repositório AGPLv3; licença pode variar por módulo |
| Open edX (https://github.com/openedx/openedx-platform) | LMS, autoria, aprendizagem, certificados e trilhas | Adaptador LMS e captura de eventos de conclusão / evidência | AGPLv3; integração por API antes de reutilizar código |
| Budibase (https://github.com/Budibase/budibase) | Construtor de automações e solicitações | Builder declarativo de eventos e aprovações em fase posterior | GPLv3, partes MPL, produtos sob BSL |
| Twenty (https://github.com/twentyhq/twenty) | Objetos flexíveis, visualizações e workflows | Aprendizado de arquitetura extensível, não copiar CRM | Conferir licença dos módulos |

**Implementar domínio próprio em vez de transplantar código**. Licenças de código aberto não são equivalentes e AGPL/GPL podem exigir obrigações não desejadas num SaaS comercial. Rever cada arquivo/versão e a forma de integração com profissional habilitado antes de copiar código.

## Evidência e qualidade científica: 5 regras
1. Separar métricas **operacionais descritivas** (ex.: turnover, conclusão) de instrumentos **psicométricos testados** (ex.: UWES-9). Uma taxa com fórmula definida NÃO passa a ser psicometricamente validada.
2. Citar fonte, versão, universo, período, filtros, denominador, exclusões e limitações ao lado de cada valor. Sem base suficiente, mostrar `—` e explicar a ausência.
3. Avaliar confiabilidade e validade local antes de usar escalas para decisões individuais; mudanças de idioma/contexto requerem análise adicional e licenciamento do instrumento.
4. Pesquisa exploratória: tratar diferenças observacionais com hipóteses e incerteza, não como efeitos causais. Atribuição de causalidade requer desenho apropriado, controle de confundidores e revisão.
5. LGPD por desenho: minimização, segregação, papéis, registro de bases legais, retenção limitada, acesso e revisão humana de análises assistidas por IA.

### Referências científicas e normativas verificadas
- ISO 30414:2025, requisitos/recomendações para reporte de capital humano nas áreas de composição, diversidade, custos, produtividade, bem-estar, recrutamento, mobilidade, rotatividade, habilidades etc. https://www.iso.org/standard/30414 ; escopo observado em https://www.iso.org/cms/%20render/live/en/sites/isoorg/contents/data/standard/08/61/86106.html . A página aberta apresenta categorias; NÃO foi analisado/adquirido texto integral da norma.
- CIPD, *People analytics* (2025): definir perguntas de negócio, combinar fontes e distinguir correlação, predição e causalidade: https://www.cipd.org/en/knowledge/factsheets/analytics-factsheet/
- CIPD, *Performance management: An introduction* (2026): gestão contínua, feedback oportuno, objetivos específicos, justiça e medidas confiáveis/válidas: https://www.cipd.org/en/knowledge/factsheets/performance-factsheet/
- CIPD, *Learning evaluation, impact and transfer* (2025): avaliação da aprendizagem vinculada a lacunas de desempenho e resultados, não só satisfação: https://www.cipd.org/en/knowledge/factsheets/evaluating-learning-factsheet/
- Sackett, Zhang, Berry & Lievens (2022), meta-análise de validade de seleção: estimativas de validade menores após revisão de correção de restrição de amplitude; entrevistas estruturadas entre métodos melhor posicionados: https://pubmed.ncbi.nlm.nih.gov/34968080/
- Schaufeli, Bakker & Salanova (2006), validade fatorial e confiabilidade da UWES-9 em estudo com 14.521 respondentes de 10 países: https://research-portal.uu.nl/en/publications/the-measurement-of-work-engagement-with-a-short-questionnaire-a-c/ . A plataforma NÃO incorpora automaticamente os itens nem afirma validade na amostra brasileira.
- NIOSH WellBQ (2026), questionário multidomínio de bem-estar ocupacional: https://www.cdc.gov/niosh/twh/php/wellbq/index.html . Orientações de uso/itens e privacidade devem ser respeitadas; tradução espanhola indicada como certificada, não validada.
- ANPD, orientação para legítimo interesse e teste de balanceamento (finalidade, necessidade, salvaguardas): https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-lanca-guia-orientativo-sobre-legitimo-interesse . A base legal válida depende da finalidade concreta, não é sempre consentimento.

## Registro de indicadores — versão 1, implementados em /api/lifecycle/analytics
| Indicador | Numerador | Denominador | Limite interpretativo |
|---|---|---|---|
| Efetivo ativo | Pessoas com status ativo | Total de colaboradores no escopo | Fotografia cadastral, qualidade da atualização |
| Conclusão de integração | Tarefas concluídas | Tarefas de integração cadastradas | Não demonstra adaptação/pertencimento ou autonomia |
| Conclusão de treinamento | Inscrições concluídas | Inscrições atribuídas | Não mede retenção do conhecimento ou mudança de comportamento |
| Atingimento de objetivos | Metas com realizado >= alvo | Metas quantitativas cadastradas | Incentiva metas fáceis se sem revisão; não equivale a valor criado |
| Rotatividade voluntária 365d | Desligamentos voluntários do período | Média aproximada entre efetivos de abertura e fechamento | Substituir pela média mensal de headcount em produção |
| Retenção 90 dias | Admitidos elegíveis que permaneceram >=90 dias | Admitidos há >=90 dias | Não representa qualidade de contratação; coorte <5 suprimida |

Todo registro retorna `value`, `numerator`, `denominator`, `method`, `suppressed`. **Atualmente, não há estimativas de intervalo de confiança, ajuste por sazonalidade ou benchmarks setoriais confiáveis.** Nenhuma métrica, isoladamente, recomenda desligamento, promoção ou salário.

## Dashboards recomendados (o que o gestor decide, e o que NÃO decide)
1. **Diretoria:** tamanho da força de trabalho, entradas/saídas por coorte, capacidade, mobilidade, custo somente quando fonte contábil auditável disponível. Drill-down autorizado; comparar períodos equivalentes.
2. **Recrutamento:** duração por etapa e cargo, qualidade de avaliação de seleção (reliabilidade entre entrevistadores), taxa de aceite, diversidade agregada *com base legal e grupos mínimos*, tempo de contratação, atendimento de SLA.
3. **Onboarding:** checklists vencidos, marcos de 7/30/60/90 dias, readiness de acesso e suporte, pesquisas de adaptação validadas quando houver licença/adequação.
4. **Aprendizagem:** necessidades por competência, cobertura e conclusão de trilhas, testes antes/depois, transferência para trabalho por supervisor, efeito estimado somente se desenho permitir.
5. **Desempenho:** evolução de objetivos relevantes, cadência de conversas, calibragem interavaliador, distribuição contextual de notas, PDI e bloqueios.
6. **Mobilidade:** movimentos internos, tempo até progressão, vagas internas preenchidas, prontidão para sucessão com critérios transparentes; não inferir potencial apenas de caixa 9-box.
7. **Clima e bem-estar:** escalas e protocolos reconhecidos, reportar agregado com limites mínimos, proteger saúde e dados sensíveis; evitar vigilância individual.
8. **Rotatividade:** cohort retention e sobrevivência por antiguidade; desligamentos voluntários/involuntários; entrevistas de saída; não predizer probabilidade individual de sair sem análise de impacto e supervisão rigorosa.

## Arquitetura — próximos domínios
- **Identity & Tenant**: Company, User, Permission, employee self-service; auth única com escopo por empresa.
- **Talent Acquisition**: Job, Application, Candidate, Interview, Scorecard, Offer.
- **Core People**: Employee, Employment, Department, EmploymentEvent, ConsentRecord, CareerEvent.
- **Onboarding**: OnboardingTemplate, OnboardingItem, Assignment, Evidence, Reminder.
- **Learning**: Course, Lesson, LearningPath, Enrollment, AssessmentAttempt, Competency, Certification.
- **Performance**: PerformanceCycle, Goal, CheckIn, Feedback, Review, Criterion, DevelopmentPlan.
- **People Analytics**: MetricDefinition, MetricSnapshot, DataLineage, QualityCheck, AuditLog. Relatórios em BI com trilha de dados.
- **Automation / Integration**: outbox, scheduled job, retries idempotentes; e-mail e LMS adaptados. Sem envio silencioso.
- **Compliance**: controle de retenção, revogação, atendimento LGPD, trilhas e logs imutáveis/revisáveis.

### Prioridades e dependências
**Entregue v0.4 (módulo local):** diretório de colaboradores, conversão do ATS para HRIS pós-oferta aceita e contratação, checklists e conclusão, catálogo de cursos/inscrições, objetivos/progresso, avaliações ponderadas, mobilidade e desligamento, painel descritivo por tenant com 6 indicadores. Adicionados fixtures artificiais da Nexa e testes.

**Próximas etapas, NÃO implementadas:** ciclos completos de PDI/OKR, LMS com conteúdo e avaliações anteriores/posteriores, pulso validado conforme instrumento e licença, gestão de remuneração/benefícios, SST, trilhas de compliance, notificação real, SSO, granularidade das permissões de gestão, auditoria e criptografia em repouso, Postgres testado em produção, operações de RH legais e folha, dashboards estatísticos longitudinais, testes reais de navegador/celular e segurança.

## Critérios de aceitação futuros
- Métricas calculadas com denominador e versão; consultas entre tenants bloqueadas, nunca combinadas.
- Cargos e equipes definem regras de visibilidade; candidato não herda indevidamente acesso à ficha de colaborador.
- Tabelas com relações tenant consistentes, migrações versionadas, testes de acesso por perfil.
- Dashboards com filtro por período e coorte, fontes auditáveis, dados ausentes explicitados.
- Não usar nota de desempenho para punições automáticas e não expor resultados sensíveis de pesquisas com grupos muito pequenos.
- Revisão jurídica LGPD, validação de instrumentos e licenças antes de dados reais.
