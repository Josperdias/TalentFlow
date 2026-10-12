import { useEffect, useState, type DragEvent, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ApiError, api } from '../api/client';
import type { ApplicationRow, Job, JobDetail as Detail, Stage } from '../api/types';
import { useAuth, useResource } from '../state';
import { ConflictDialog, Empty, ErrorState, Field, Modal, PageHead, Skeleton, Tag } from '../components/ui';
import { Avatar } from '../components/viz';
import { fitLabel, fmtDate, JOB_STATUS } from '../format';

export default function JobDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const res = useResource<Detail>(s => api.get(`/jobs/${id}`, s), [id], ['job', 'application', 'job_stage', 'interview', 'scorecard']);
  const [conflict, setConflict] = useState('');
  const [editing, setEditing] = useState(false);
  const [pendingMove, setPendingMove] = useState<{ app: ApplicationRow; stage: Stage } | null>(null);
  const [toast, setToast] = useState('');
  const [over, setOver] = useState<number | null>(null);
  const canEdit = user?.role === 'admin' || user?.role === 'recruiter';
  const canMove = canEdit || user?.role === 'manager';
  const canApprove = user?.role === 'admin' || user?.role === 'manager';

  if (res.error && !res.data) return <><PageHead eyebrow="Vagas" title="Vaga" /><ErrorState error={res.error} onRetry={res.reload} /></>;
  if (!res.data) return <Skeleton rows={8} />;
  const { job, stages, applications } = res.data;

  const move = async (app: ApplicationRow, stage: Stage, reason = '') => {
    setToast('');
    try {
      await api.post(`/applications/${app.id}/move`, { stage_id: stage.id, reason }, app.version);
      setToast(`${app.candidate.name} movido para ${stage.name}.`);
      res.reload();
    } catch (e) {
      if (e instanceof ApiError && e.isConflict) { setConflict(e.message); res.reload(); } else setToast((e as Error).message);
    }
  };
  const requestMove = (app: ApplicationRow, stage: Stage) => {
    if (stage.id === app.stage_id) return;
    if (stage.kind !== 'active') setPendingMove({ app, stage }); else void move(app, stage);
  };
  const decide = async (decision: 'approved' | 'rejected') => {
    try { await api.post(`/jobs/${job.id}/approve`, { decision }); res.reload(); } catch (e) { setToast((e as Error).message); }
  };
  const onDrop = (stage: Stage) => (e: DragEvent) => {
    e.preventDefault(); setOver(null);
    const app = applications.find(a => a.id === Number(e.dataTransfer.getData('text/plain')));
    if (app) requestMove(app, stage);
  };

  return (
    <>
      <PageHead eyebrow={<Link to="/vagas">Vagas</Link>} title={job.title} lead={`${job.code} · ${job.department} · ${job.location} · ${job.modality} · ${job.seniority}`}>
        <Tag tone={JOB_STATUS[job.status]?.tone}>{JOB_STATUS[job.status]?.label}</Tag>
        {job.status === 'approval' && canApprove && <>
          <button className="btn" onClick={() => decide('rejected')}>Recusar</button>
          <button className="btn primary" onClick={() => decide('approved')}>Aprovar vaga</button>
        </>}
        {canEdit && <button className="btn" onClick={() => setEditing(true)}>Editar</button>}
      </PageHead>

      <p className="muted" style={{ marginBottom: 16 }}>Prazo {fmtDate(job.due_date)} · {job.positions} posição(ões) · versão {job.version}</p>
      <div aria-live="polite">{toast && <div className="notice info" role="status">{toast}</div>}</div>

      {stages.length === 0 || applications.length === 0 ? <Empty title="Nenhuma candidatura nesta vaga">Candidaturas recebidas pela página de carreiras ou cadastradas por recrutadores aparecem aqui.</Empty> : (
        <div className="pipeline" role="list" aria-label="Pipeline da vaga">
          {stages.map(stage => {
            const apps = applications.filter(a => a.stage_id === stage.id);
            return (
              <section key={stage.id} role="listitem" className={`col${over === stage.id ? ' over' : ''}`} aria-label={`${stage.name}: ${apps.length} candidatura(s)`}
                onDragOver={e => { if (canMove) { e.preventDefault(); setOver(stage.id); } }} onDragLeave={() => setOver(null)} onDrop={canMove ? onDrop(stage) : undefined}>
                <header><span className="col-name"><i className="col-dot" />{stage.name}</span><span className="muted num">{apps.length}</span></header>
                <ul>
                  {apps.map(a => (
                    <li key={a.id} className="card" draggable={canMove} onDragStart={e => e.dataTransfer.setData('text/plain', String(a.id))}>
                      <div className="card-top"><Avatar name={a.candidate.name} size={34} /><div><b>{a.candidate.name}</b><span className="muted">{a.candidate.title || a.candidate.location || '—'}</span></div></div>
                      <span><Tag tone={a.fit >= 75 ? 'positive' : a.fit >= 50 ? 'info' : ''}>Fit {fitLabel(a.fit)} · {a.fit}</Tag></span>
                      {canMove && (
                        <label className="field"><span className="sr-only">Mover {a.candidate.name} para</span>
                          <select value={a.stage_id} onChange={e => requestMove(a, stages.find(s => s.id === Number(e.target.value))!)}>
                            {stages.map(s => <option key={s.id} value={s.id}>{s.id === a.stage_id ? `Etapa: ${s.name}` : `Mover para ${s.name}`}</option>)}
                          </select>
                        </label>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            );
          })}
        </div>
      )}

      <ReasonDialog pending={pendingMove} onClose={() => setPendingMove(null)} onConfirm={reason => { const p = pendingMove!; setPendingMove(null); void move(p.app, p.stage, reason); }} />
      <EditJob job={job} open={editing} onClose={() => setEditing(false)} onSaved={() => { setEditing(false); res.reload(); }} onConflict={m => { setEditing(false); setConflict(m); res.reload(); }} />
      <ConflictDialog open={!!conflict} message={conflict} onReload={res.reload} onClose={() => setConflict('')} />
    </>
  );
}

function ReasonDialog({ pending, onClose, onConfirm }: { pending: { app: ApplicationRow; stage: Stage } | null; onClose: () => void; onConfirm: (r: string) => void }) {
  const [reason, setReason] = useState('');
  return (
    <Modal open={!!pending} onClose={onClose} title={pending?.stage.kind === 'hired' ? 'Registrar contratação' : 'Registrar reprovação'}>
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); onConfirm(reason.trim()); setReason(''); }} style={{ padding: 0 }}>
        <p>Decisões finais exigem um motivo, que fica no histórico e na auditoria.</p>
        <Field label={`Motivo para ${pending?.app.candidate.name ?? ''}`}><textarea required minLength={3} value={reason} onChange={e => setReason(e.target.value)} /></Field>
        <footer><button type="button" className="btn" onClick={onClose}>Cancelar</button><button className="btn primary">Confirmar</button></footer>
      </form>
    </Modal>
  );
}

function EditJob({ job, open, onClose, onSaved, onConflict }: { job: Job; open: boolean; onClose: () => void; onSaved: () => void; onConflict: (m: string) => void }) {
  // A edição fica presa à versão em que foi aberta: se outra pessoa salvar antes, o servidor responde 409
  // e nada é sobrescrito em silêncio (a tela ao fundo pode atualizar, o formulário não "rebaseia").
  const [base, setBase] = useState<Job>(job);
  const [f, setF] = useState({ title: job.title, department: job.department, location: job.location, description: job.description, requirements: job.requirements, due_date: job.due_date });
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (open) { setBase(job); setF({ title: job.title, department: job.department, location: job.location, description: job.description, requirements: job.requirements, due_date: job.due_date }); setError(''); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);
  const changedElsewhere = open && job.version !== base.version;
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    try { await api.patch(`/jobs/${job.id}`, f, base.version); onSaved(); }
    catch (err) { if (err instanceof ApiError && err.isConflict) onConflict(err.message); else setError((err as Error).message); }
    finally { setBusy(false); }
  };
  return (
    <Modal open={open} onClose={onClose} title="Editar vaga">
      <form onSubmit={submit} style={{ padding: 0 }}>
        {changedElsewhere && <div className="notice attention" role="status"><b>Alterada por outra pessoa</b>Esta vaga foi atualizada enquanto você editava. Ao salvar, você será avisado do conflito e poderá revisar a versão atual.</div>}
        <div className="form-grid">
          <div className="wide"><Field label="Título"><input required minLength={3} value={f.title} onChange={set('title')} /></Field></div>
          <Field label="Área"><input value={f.department} onChange={set('department')} /></Field>
          <Field label="Local"><input value={f.location} onChange={set('location')} /></Field>
          <Field label="Prazo"><input type="date" value={f.due_date} onChange={set('due_date')} /></Field>
          <div className="wide"><Field label="Descrição"><textarea value={f.description} onChange={set('description')} /></Field></div>
          <div className="wide"><Field label="Requisitos"><textarea value={f.requirements} onChange={set('requirements')} /></Field></div>
        </div>
        {error && <div className="notice critical" role="alert">{error}</div>}
        <footer><button type="button" className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy}>{busy ? 'Salvando…' : 'Salvar alterações'}</button></footer>
      </form>
    </Modal>
  );
}
