import { useState, type FormEvent } from 'react';
import { api } from '../api/client';
import type { Employee, Leave } from '../api/types';
import { useAuth, useResource } from '../state';
import { Empty, ErrorState, Field, Modal, PageHead, Skeleton, Tag } from '../components/ui';
import { fmtDate, LEAVE_KIND, LEAVE_STATUS, today } from '../format';

export default function Leaves() {
  const { user } = useAuth();
  const [status, setStatus] = useState('');
  const [creating, setCreating] = useState(false);
  const [msg, setMsg] = useState('');
  const res = useResource<Leave[]>(s => api.get(`/workforce/leaves?status=${status}`, s), [status], ['leave_request']);
  const canDecide = user?.role === 'admin' || user?.role === 'manager';
  const decide = async (l: Leave, decision: 'approved' | 'rejected') => {
    try { await api.post(`/workforce/leaves/${l.id}/decide`, { decision }); setMsg(''); res.reload(); }
    catch (e) { setMsg((e as Error).message); res.reload(); }
  };
  return (
    <>
      <PageHead eyebrow="Pessoas" title="Ausências" lead="Férias e afastamentos registrados. Não substitui cálculo de folha ou conformidade trabalhista.">
        <button className="btn primary" onClick={() => setCreating(true)}>Nova solicitação</button>
      </PageHead>
      <div className="toolbar"><Field label="Situação"><select value={status} onChange={e => setStatus(e.target.value)}>
        <option value="">Todas</option>{Object.entries(LEAVE_STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}</select></Field></div>
      <div aria-live="polite">{msg && <div className="notice critical" role="alert">{msg}</div>}</div>
      {res.error && !res.data ? <ErrorState error={res.error} onRetry={res.reload} /> : !res.data ? <Skeleton /> :
        !res.data.length ? <Empty title="Nenhuma solicitação" /> : (
          <div className="table-wrap"><table className="grid stack">
            <thead><tr><th>Colaborador</th><th>Tipo</th><th>Período</th><th className="num">Dias</th><th>Situação</th><th /></tr></thead>
            <tbody>{res.data.map(l => (
              <tr key={l.id}><td data-label="Colaborador">{l.employee}<span className="muted"> · {l.department}</span></td><td data-label="Tipo">{LEAVE_KIND[l.kind] ?? l.kind}</td>
                <td data-label="Período">{fmtDate(l.starts_on)} – {fmtDate(l.ends_on)}</td><td data-label="Dias" className="num">{l.days}</td>
                <td data-label="Situação"><Tag tone={LEAVE_STATUS[l.status].tone}>{LEAVE_STATUS[l.status].label}</Tag></td>
                <td className="num">{l.status === 'pending' && canDecide && <span className="actions" style={{ justifyContent: 'flex-end' }}>
                  <button className="btn sm" onClick={() => decide(l, 'rejected')}>Recusar</button><button className="btn sm primary" onClick={() => decide(l, 'approved')}>Aprovar</button></span>}</td></tr>))}</tbody>
          </table></div>
        )}
      <NewLeave open={creating} onClose={() => setCreating(false)} onSaved={() => { setCreating(false); res.reload(); }} />
    </>
  );
}

function NewLeave({ open, onClose, onSaved }: { open: boolean; onClose: () => void; onSaved: () => void }) {
  const emps = useResource<Employee[]>(s => (open ? api.get('/lifecycle/employees', s) : Promise.resolve([])), [open]);
  const [f, setF] = useState({ employee_id: '', kind: 'vacation', starts_on: today(), ends_on: today(), reason: '' });
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    try { await api.post('/workforce/leaves', { ...f, employee_id: Number(f.employee_id) }); onSaved(); }
    catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  };
  return (
    <Modal open={open} onClose={onClose} title="Nova solicitação de ausência">
      <form onSubmit={submit} style={{ padding: 0 }}>
        <div className="form-grid">
          <div className="wide"><Field label="Colaborador"><select required value={f.employee_id} onChange={set('employee_id')}><option value="">Selecione…</option>
            {(emps.data ?? []).filter(e => e.status === 'active').map(e => <option key={e.id} value={e.id}>{e.name}</option>)}</select></Field></div>
          <Field label="Tipo"><select value={f.kind} onChange={set('kind')}>{Object.entries(LEAVE_KIND).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></Field>
          <Field label="Início"><input type="date" required value={f.starts_on} onChange={set('starts_on')} /></Field>
          <Field label="Fim"><input type="date" required min={f.starts_on} value={f.ends_on} onChange={set('ends_on')} /></Field>
          <div className="wide"><Field label="Observação"><textarea value={f.reason} onChange={set('reason')} maxLength={2000} /></Field></div>
        </div>
        {error && <div className="notice critical" role="alert">{error}</div>}
        <footer><button type="button" className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy}>{busy ? 'Enviando…' : 'Registrar'}</button></footer>
      </form>
    </Modal>
  );
}
