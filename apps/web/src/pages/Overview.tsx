import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Dashboard, Insights, Trend } from '../api/types';
import { useAuth, useResource } from '../state';
import { Empty, ErrorState, PageHead, Skeleton } from '../components/ui';
import { Icon } from '../components/icons';
import { Donut, Kpi, TrendChart } from '../components/viz';

const fmtLong = new Intl.DateTimeFormat('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' });

export default function Overview() {
  const { user } = useAuth();
  const staff = user?.role !== 'interviewer';
  const dash = useResource<Dashboard>(s => api.get('/dashboard', s), [], ['job', 'application', 'interview', 'offer', 'task']);
  const ins = useResource<Insights | null>(s => (staff ? api.get<Insights>('/workforce/insights', s) : Promise.resolve(null)), [staff], ['employee', 'development_plan', 'leave_request']);

  const trend = useResource<Trend>(s => api.get('/dashboard/trend', s), [], ['application', 'job_stage']);

  if (dash.loading && !dash.data) return <><PageHead eyebrow="Visão geral" title="Carregando…" /><div className="kpis" aria-busy="true">{Array.from({ length: 5 }, (_, n) => <div key={n} className="kpi skel" style={{ animationDelay: `${n * 60}ms` }}><div className="skeleton" style={{ width: '55%' }} /><div className="skeleton" style={{ height: 34, width: '40%', margin: '14px 0' }} /><div className="skeleton" style={{ width: '75%' }} /></div>)}</div></>;
  if (dash.error && !dash.data) return <><PageHead eyebrow="Visão geral" title="Visão geral" /><ErrorState error={dash.error} onRetry={dash.reload} /></>;
  const m = dash.data!.metrics;
  const maxStage = Math.max(1, ...dash.data!.stages.map(s => s.value));
  const i = ins.data;
  const attention: { to: string; text: string }[] = [];
  if (m.late_jobs > 0) attention.push({ to: '/vagas', text: `${m.late_jobs} vaga(s) aberta(s) com prazo vencido` });
  if (m.jobs_approval > 0) attention.push({ to: '/vagas', text: `${m.jobs_approval} vaga(s) aguardando aprovação` });
  if (i && i.pending_leaves > 0) attention.push({ to: '/ausencias', text: `${i.pending_leaves} solicitação(ões) de ausência pendente(s)` });
  if (m.pending_tasks > 0) attention.push({ to: '/vagas', text: `${m.pending_tasks} tarefa(s) de seleção em aberto` });

  const status = [
    { label: 'Ativas', value: m.candidates_active, color: '#5846D4' },
    { label: 'Contratadas', value: m.hired, color: '#12906A' },
    { label: 'Reprovadas', value: m.rejected, color: '#C0506A' }
  ];
  const series = trend.data && trend.data.points.length > 1 ? trend.data.points : undefined;
  const statusTotal = status.reduce((a, x) => a + x.value, 0);

  return (
    <>
      <PageHead eyebrow={fmtLong.format(new Date())} title={`Olá, ${user?.name.split(' ')[0]}`} lead="Situação atual da sua empresa, calculada a partir dos registros do servidor." />

      <section aria-labelledby="h-rec">
        <h2 id="h-rec" className="eyebrow">Recrutamento</h2>
        <div className="kpis">
          <Kpi delay={0} icon="jobs" label="Vagas abertas" count={{ to: m.jobs_open }} note={`${m.jobs_approval} em aprovação`} />
          <Kpi delay={60} icon="people" tone="info" label="Candidaturas ativas" count={{ to: m.candidates_active }} note={`${m.interviews} entrevista(s) agendada(s)`} trend={series?.map(p => p.applications)} trendLabel="Candidaturas recebidas por mês" />
          <Kpi delay={120} icon="check" tone="positive" label="Contratações" count={{ to: m.hired }} note={`${m.rejected} reprovação(ões) registradas`} trend={series?.map(p => p.hired)} trendLabel="Contratações por mês" />
          <Kpi delay={180} icon="clock" tone="attention" label="Tempo até contratar" {...(m.hired === 0 ? { value: '—' } : { count: { to: m.avg_time_hire, decimals: 1 } })} note={m.hired === 0 ? 'Sem contratações para calcular' : 'dias, média das contratações registradas'} />
          <Kpi delay={240} icon="trend" label="Conversão" {...(m.candidates_active + m.hired + m.rejected === 0 ? { value: '—' } : { count: { to: m.conversion, decimals: 1, suffix: '%' } })} note="contratados ÷ candidaturas totais" />
        </div>
      </section>

      {staff && (
        <section aria-labelledby="h-pes" className="section">
          <h2 id="h-pes" className="eyebrow">Pessoas</h2>
          {ins.error && !i ? <ErrorState error={ins.error} onRetry={ins.reload} /> : !i ? <Skeleton rows={3} /> : (
            <div className="kpis three">
              <Kpi delay={0} icon="team" label="Colaboradores ativos" count={{ to: i.active }} note={`de ${i.population} registrados`} />
              <Kpi delay={60} icon="plan" tone="positive" label="Planos de desenvolvimento concluídos" value={i.development_completion.denominator === 0 ? '—' : `${i.development_completion.numerator}/${i.development_completion.denominator}`} note={i.development_completion.interpretation} />
              <Kpi delay={120} icon="leave" tone="attention" label="Ausências pendentes" count={{ to: i.pending_leaves }} note="aguardando decisão" />
            </div>
          )}
        </section>
      )}

      <section className="panel section" aria-labelledby="h-trd">
        <div className="panel-head"><h2 id="h-trd" className="panel-title">Evolução de candidaturas</h2><span className="faint">últimos 12 meses · dados reais do servidor</span></div>
        {trend.error && !trend.data ? <ErrorState error={trend.error} onRetry={trend.reload} /> : !trend.data ? <Skeleton rows={4} /> : <TrendChart points={trend.data.points} />}
        {trend.data?.note && <p className="faint foot-note" style={{ marginTop: 12 }}>{trend.data.note}</p>}
      </section>

      <div className="split section">
        <section className="panel" aria-labelledby="h-fun">
          <h2 id="h-fun" className="panel-title">Funil de candidaturas por etapa</h2>
          {dash.data!.stages.length === 0 ? <Empty title="Sem candidaturas">Cadastre uma vaga e receba candidaturas para ver o funil.</Empty> : (
            <div className="bars" role="list">
              {dash.data!.stages.map((s, n) => (
                <div className="bar-row" role="listitem" key={s.name}>
                  <span>{s.name}</span>
                  <div className="bar-track" aria-hidden="true"><div className="bar-fill" style={{ width: `${(s.value / maxStage) * 100}%`, animationDelay: `${n * 70}ms` }} /></div>
                  <span className="num">{s.value}</span>
                </div>
              ))}
            </div>
          )}
        </section>

        <div className="stack-col">
          <section className="panel" aria-labelledby="h-sta">
            <h2 id="h-sta" className="panel-title">Situação das candidaturas</h2>
            <div className="donut-row">
              <Donut slices={status} centerLabel="candidaturas" />
              <ul className="legend">
                {status.map(x => <li key={x.label}><i style={{ background: x.color }} /><span>{x.label}</span><b className="num">{x.value}</b><small className="faint">{statusTotal === 0 ? '—' : `${Math.round((x.value / statusTotal) * 100)}%`}</small></li>)}
              </ul>
            </div>
          </section>

          <section className="panel" aria-labelledby="h-att">
            <h2 id="h-att" className="panel-title">Requer atenção</h2>
            {attention.length === 0 ? <p className="muted">Nada pendente no momento.</p> : (
              <ul className="attention-list">
                {attention.map(a => <li key={a.text}><Link to={a.to}><span className="ico"><Icon name="alert" size={16} /></span><span>{a.text}</span><Icon name="arrow" size={16} /></Link></li>)}
              </ul>
            )}
          </section>
        </div>
      </div>
      {i && i.limits.length > 0 && <p className="faint foot-note">{i.limits.join(' · ')}</p>}
    </>
  );
}
