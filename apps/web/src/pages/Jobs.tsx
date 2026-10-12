import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { Job } from '../api/types';
import { useAuth, useResource } from '../state';
import { Empty, ErrorState, Field, Modal, PageHead, Skeleton, Tag } from '../components/ui';
import { fmtDate, fmtMoney, JOB_STATUS } from '../format';

export default function Jobs() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [q, setQ] = useState(''); const [status, setStatus] = useState('');
  const [creating, setCreating] = useState(false);
  const jobs = useResource<Job[]>(s => api.get(`/jobs?q=${encodeURIComponent(q)}&status=${status}`, s), [q, status], ['job', 'application']);
  const canEdit = user?.role === 'admin' || user?.role === 'recruiter';

  return (
    <>
      <PageHead eyebrow="Recrutamento" title="Vagas" lead="Requisições, vagas abertas e seus pipelines.">
        {canEdit && <button className="btn primary" onClick={() => setCreating(true)}>Nova vaga</button>}
      </PageHead>
      <div className="toolbar" role="search">
        <Field label="Buscar por título"><input value={q} onChange={e => setQ(e.target.value)} placeholder="Ex.: analista" /></Field>
        <Field label="Situação">
          <select value={status} onChange={e => setStatus(e.target.value)}>
            <option value="">Todas</option>{Object.entries(JOB_STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </Field>
      </div>
      {jobs.error && !jobs.data ? <ErrorState error={jobs.error} onRetry={jobs.reload} /> :
        jobs.loading && !jobs.data ? <Skeleton /> :
        !jobs.data!.length ? <Empty title="Nenhuma vaga encontrada">{canEdit ? 'Crie a primeira vaga para iniciar um processo seletivo.' : 'Não há vagas atribuídas a você.'}</Empty> : (
          <div className="table-wrap">
            <table className="grid stack">
              <thead><tr><th>Código</th><th>Vaga</th><th>Área</th><th>Local</th><th>Faixa salarial</th><th>Prazo</th><th>Situação</th><th className="num">Candidaturas</th></tr></thead>
              <tbody>
                {jobs.data!.map(j => (
                  <tr key={j.id}>
                    <td data-label="Código" className="mono">{j.code}</td>
                    <td data-label="Vaga"><Link className="cell-link" to={`/vagas/${j.id}`}>{j.title}</Link></td>
                    <td data-label="Área">{j.department}</td>
                    <td data-label="Local">{j.location} · {j.modality}</td>
                    <td data-label="Faixa" className="nw">{j.salary_max > 0 ? `${fmtMoney(j.salary_min)} – ${fmtMoney(j.salary_max)}` : '—'}</td>
                    <td data-label="Prazo" className="nw">{fmtDate(j.due_date)}</td>
                    <td data-label="Situação"><Tag tone={JOB_STATUS[j.status]?.tone}>{JOB_STATUS[j.status]?.label ?? j.status}</Tag></td>
                    <td data-label="Candidaturas" className="num">{j.applications}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      <NewJob open={creating} onClose={() => setCreating(false)} onCreated={id => nav(`/vagas/${id}`)} />
    </>
  );
}

function NewJob({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: (id: number) => void }) {
  const [f, setF] = useState({ title: '', department: '', location: '', modality: 'Híbrido', seniority: 'Pleno', description: '', requirements: '', status: 'approval' });
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const set = (k: string) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    try {
      const body = Object.fromEntries(Object.entries(f).filter(([, v]) => v !== ''));
      const job = await api.post<Job>('/jobs', body);
      onClose(); onCreated(job.id);
    } catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  };
  return (
    <Modal open={open} onClose={onClose} title="Nova vaga">
      <form onSubmit={submit} style={{ padding: 0 }}>
        <div className="form-grid">
          <div className="wide"><Field label="Título da vaga"><input required minLength={3} value={f.title} onChange={set('title')} /></Field></div>
          <Field label="Área"><input value={f.department} onChange={set('department')} placeholder="Tecnologia" /></Field>
          <Field label="Local"><input value={f.location} onChange={set('location')} placeholder="Brasília, DF" /></Field>
          <Field label="Modalidade"><select value={f.modality} onChange={set('modality')}><option>Presencial</option><option>Híbrido</option><option>Remoto</option></select></Field>
          <Field label="Senioridade"><select value={f.seniority} onChange={set('seniority')}><option>Júnior</option><option>Pleno</option><option>Sênior</option></select></Field>
          <div className="wide"><Field label="Requisitos"><textarea value={f.requirements} onChange={set('requirements')} /></Field></div>
          <Field label="Início como"><select value={f.status} onChange={set('status')}><option value="approval">Em aprovação</option><option value="open">Aberta</option></select></Field>
        </div>
        {error && <div className="notice critical" role="alert">{error}</div>}
        <footer><button type="button" className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy}>{busy ? 'Salvando…' : 'Criar vaga'}</button></footer>
      </form>
    </Modal>
  );
}
