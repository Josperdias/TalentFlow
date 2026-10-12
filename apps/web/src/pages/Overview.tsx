import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Dashboard, Insights } from '../api/types';
import { useAuth, useResource } from '../state';
import { Empty, ErrorState, PageHead, Skeleton } from '../components/ui';

const fmtLong = new Intl.DateTimeFormat('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' });

/** Valor com denominador zero ou amostra vazia aparece como "—", nunca como 0 indevido. */
const orDash = (n: number | null | undefined, empty: boolean) => (empty || n == null ? '—' : String(n));

export default function Overview() {
  const { user } = useAuth();
  const staff = user?.role !== 'interviewer';
  const dash = useResource<Dashboard>(s => api.get('/dashboard', s), [], ['job', 'application', 'interview', 'offer', 'task']);
  const ins = useResource<Insights | null>(s => (staff ? api.get<Insights>('/workforce/insights', s) : Promise.resolve(null)), [staff], ['employee', 'development_plan', 'leave_request']);

  if (dash.loading && !dash.data) return <><PageHead eyebrow="Visão geral" title="Carregando…" /><Skeleton rows={6} /></>;
  if (dash.error && !dash.data) return <><PageHead eyebrow="Visão geral" title="Visão geral" /><ErrorState error={dash.error} onRetry={dash.reload} /></>;
  const m = dash.data!.metrics;
  const maxStage = Math.max(1, ...dash.data!.stages.map(s => s.value));
  const i = ins.data;
  const attention: { to: string; text: string }[] = [];
  if (m.late_jobs > 0) attention.push({ to: '/vagas', text: `${m.late_jobs} vaga(s) aberta(s) com prazo vencido` });
  if (m.jobs_approval > 0) attention.push({ to: '/vagas', text: `${m.jobs_approval} vaga(s) aguardando aprovação` });
  if (i && i.pending_leaves > 0) attention.push({ to: '/ausencias', text: `${i.pending_leaves} solicitação(ões) de ausência pendente(s)` });
  if (m.pending_tasks > 0) attention.push({ to: '/vagas', text: `${m.pending_tasks} tarefa(s) de seleção em aberto` });

  return (
    <>
      <PageHead eyebrow={fmtLong.format(new Date())} title={`Olá, ${user?.name.split(' ')[0]}`} lead="Situação atual da sua empresa, calculada a partir dos registros do servidor." />
      <div className="briefing">
        <section aria-labelledby="h-rec">
          <h2 id="h-rec" className="eyebrow">Recrutamento</h2>
          <table className="ledger">
            <tbody>
              <tr><th scope="row">Vagas abertas</th><td className="fig">{m.jobs_open}</td><td className="note">{m.jobs_approval} em aprovação</td></tr>
              <tr><th scope="row">Candidaturas ativas</th><td className="fig">{m.candidates_active}</td><td className="note">{m.interviews} entrevista(s) agendada(s)</td></tr>
              <tr><th scope="row">Contratações</th><td className="fig">{m.hired}</td><td className="note">{m.rejected} reprovação(ões) registradas</td></tr>
              <tr><th scope="row">Tempo até contratar</th><td className="fig">{orDash(m.avg_time_hire, m.hired === 0)}</td><td className="note">{m.hired === 0 ? 'Sem contratações para calcular' : 'dias, média das contratações registradas'}</td></tr>
              <tr><th scope="row">Conversão</th><td className="fig">{m.candidates_active + m.hired + m.rejected === 0 ? '—' : `${m.conversion}%`}</td><td className="note">contratados ÷ candidaturas totais</td></tr>
            </tbody>
          </table>

          {staff && (
            <>
              <h2 className="eyebrow" style={{ marginTop: 32 }}>Pessoas</h2>
              {ins.error && !i ? <ErrorState error={ins.error} onRetry={ins.reload} /> : !i ? <Skeleton rows={3} /> : (
                <table className="ledger">
                  <tbody>
                    <tr><th scope="row">Colaboradores ativos</th><td className="fig">{i.active}</td><td className="note">de {i.population} registrados</td></tr>
                    <tr><th scope="row">Planos de desenvolvimento concluídos</th><td className="fig">{i.development_completion.denominator === 0 ? '—' : `${i.development_completion.numerator}/${i.development_completion.denominator}`}</td><td className="note">{i.development_completion.interpretation}</td></tr>
                    <tr><th scope="row">Ausências pendentes</th><td className="fig">{i.pending_leaves}</td><td className="note">aguardando decisão</td></tr>
                  </tbody>
                </table>
              )}
            </>
          )}
        </section>

        <aside aria-label="Funil e atenção">
          <h2 className="eyebrow">Funil de candidaturas por etapa</h2>
          {dash.data!.stages.length === 0 ? <Empty title="Sem candidaturas">Cadastre uma vaga e receba candidaturas para ver o funil.</Empty> : (
            <div className="bars" role="list">
              {dash.data!.stages.map(s => (
                <div className="bar-row" role="listitem" key={s.name}>
                  <span>{s.name}</span>
                  <div className="bar-track" aria-hidden="true"><div className="bar-fill" style={{ width: `${(s.value / maxStage) * 100}%` }} /></div>
                  <span className="num">{s.value}</span>
                </div>
              ))}
            </div>
          )}
          <h2 className="eyebrow" style={{ marginTop: 32 }}>Requer atenção</h2>
          {attention.length === 0 ? <p className="muted">Nada pendente no momento.</p> : (
            <ul style={{ paddingLeft: 18, margin: 0, display: 'grid', gap: 6 }}>
              {attention.map(a => <li key={a.text}><Link to={a.to}>{a.text}</Link></li>)}
            </ul>
          )}
          {i && i.limits.length > 0 && <p className="faint" style={{ marginTop: 32, fontSize: 12 }}>{i.limits.join(' · ')}</p>}
        </aside>
      </div>
    </>
  );
}
