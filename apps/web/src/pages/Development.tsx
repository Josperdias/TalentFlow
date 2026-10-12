import { useState } from 'react';
import { ApiError, api } from '../api/client';
import type { Plan } from '../api/types';
import { useResource } from '../state';
import { ConflictDialog, Empty, ErrorState, Field, Modal, PageHead, Skeleton, Tag } from '../components/ui';
import { fmtDate } from '../format';

export default function Development() {
  const [status, setStatus] = useState('active');
  const [conflict, setConflict] = useState('');
  const [msg, setMsg] = useState('');
  const res = useResource<Plan[]>(s => api.get(`/workforce/plans?status=${status}`, s), [status], ['development_plan']);

  const [ev, setEv] = useState<{ p: Plan; index: number } | null>(null);
  const [evidence, setEvidence] = useState('');
  const toggle = async (p: Plan, index: number, done: boolean, evidence = '') => {
    try { await api.post(`/workforce/plans/${p.id}/action`, { index, done, evidence }, p.version); setMsg(''); res.reload(); }
    catch (e) { if (e instanceof ApiError && e.isConflict) { setConflict(e.message); res.reload(); } else setMsg((e as Error).message); }
  };

  return (
    <>
      <PageHead eyebrow="Pessoas" title="Desenvolvimento" lead="Planos de desenvolvimento individual. O progresso mede execução das atividades, não ganho de competência." />
      <div className="toolbar"><Field label="Situação"><select value={status} onChange={e => setStatus(e.target.value)}>
        <option value="active">Em andamento</option><option value="completed">Concluídos</option><option value="">Todos</option></select></Field></div>
      <div aria-live="polite">{msg && <div className="notice critical" role="alert">{msg}</div>}</div>
      {res.error && !res.data ? <ErrorState error={res.error} onRetry={res.reload} /> : !res.data ? <Skeleton /> :
        !res.data.length ? <Empty title="Nenhum plano neste filtro" /> : (
          <div style={{ display: 'grid', gap: 16 }}>
            {res.data.map(p => (
              <article key={p.id} className="table-wrap" style={{ padding: 16 }} aria-labelledby={`plan-${p.id}`}>
                <header style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <div><h2 id={`plan-${p.id}`}>{p.title}</h2><p className="muted">{p.employee}{p.competency ? ` · ${p.competency}` : ''} · prazo {fmtDate(p.due_date)}</p></div>
                  <div><Tag tone={p.status === 'completed' ? 'positive' : 'info'}>{p.status === 'completed' ? 'Concluído' : 'Em andamento'}</Tag> <span className="mono">{p.progress}%</span></div>
                </header>
                <div className="bar-track" style={{ margin: '12px 0' }} role="progressbar" aria-valuenow={p.progress} aria-valuemin={0} aria-valuemax={100} aria-label={`Progresso de ${p.title}`}><div className="bar-fill" style={{ width: `${p.progress}%` }} /></div>
                <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: 6 }}>
                  {p.actions.map((a, i) => (
                    <li key={i} style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}>
                      <input type="checkbox" id={`a-${p.id}-${i}`} checked={a.done} disabled={p.status === 'archived'} onChange={e => (e.target.checked ? (setEvidence(''), setEv({ p, index: i })) : toggle(p, i, false))} />
                      <label htmlFor={`a-${p.id}-${i}`}>{a.title}{a.evidence && <span className="muted"> — {a.evidence}</span>}</label>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        )}
      <Modal open={!!ev} onClose={() => setEv(null)} title="Concluir atividade">
        <form style={{ padding: 0 }} onSubmit={e => { e.preventDefault(); const t = ev!; setEv(null); void toggle(t.p, t.index, true, evidence.trim()); }}>
          <p>{ev?.p.actions[ev.index]?.title}</p>
          <Field label="Evidência (opcional)"><textarea value={evidence} maxLength={1000} onChange={e => setEvidence(e.target.value)} /></Field>
          <footer><button type="button" className="btn" onClick={() => setEv(null)}>Cancelar</button><button className="btn primary">Marcar como concluída</button></footer>
        </form>
      </Modal>
      <ConflictDialog open={!!conflict} message={conflict} onReload={res.reload} onClose={() => setConflict('')} />
    </>
  );
}
