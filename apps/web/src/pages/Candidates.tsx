import { useState } from 'react';
import { api } from '../api/client';
import type { ApplicationRow, Candidate } from '../api/types';
import { useResource } from '../state';
import { Empty, ErrorState, Field, Modal, PageHead, Skeleton, Tag } from '../components/ui';
import { fitLabel, fmtDate } from '../format';

export default function Candidates() {
  const [q, setQ] = useState('');
  const [open, setOpen] = useState<number | null>(null);
  const list = useResource<Candidate[]>(s => api.get(`/candidates?q=${encodeURIComponent(q)}`, s), [q], ['candidate', 'application']);
  return (
    <>
      <PageHead eyebrow="Recrutamento" title="Candidatos" lead="Banco de talentos da empresa. Você só vê pessoas ligadas às vagas que pode acessar." />
      <div className="toolbar" role="search"><Field label="Buscar por nome, cargo ou habilidade"><input value={q} onChange={e => setQ(e.target.value)} /></Field></div>
      {list.error && !list.data ? <ErrorState error={list.error} onRetry={list.reload} /> : !list.data ? <Skeleton /> :
        !list.data.length ? <Empty title="Nenhum candidato encontrado" /> : (
          <div className="table-wrap">
            <table className="grid stack">
              <thead><tr><th>Nome</th><th>Cargo atual</th><th>Local</th><th>Origem</th><th className="num">Experiência</th><th>Cadastro</th></tr></thead>
              <tbody>{list.data.map(c => (
                <tr key={c.id}>
                  <td data-label="Nome"><button className="btn quiet" style={{ padding: 0, color: 'var(--c-ink)', fontWeight: 500 }} onClick={() => setOpen(c.id)}>{c.name}</button></td>
                  <td data-label="Cargo">{c.title || '—'}</td><td data-label="Local">{c.location || '—'}</td><td data-label="Origem">{c.source}</td>
                  <td data-label="Experiência" className="num">{c.experience_years} ano(s)</td><td data-label="Cadastro">{fmtDate(c.created_at)}</td>
                </tr>))}</tbody>
            </table>
          </div>
        )}
      <Detail id={open} onClose={() => setOpen(null)} />
    </>
  );
}

function Detail({ id, onClose }: { id: number | null; onClose: () => void }) {
  const res = useResource<{ candidate: Candidate; applications: ApplicationRow[] } | null>(s => (id ? api.get(`/candidates/${id}`, s) : Promise.resolve(null)), [id]);
  const d = res.data;
  return (
    <Modal open={id !== null} onClose={onClose} title={d?.candidate.name ?? 'Candidato'}>
      {res.error ? <ErrorState error={res.error} onRetry={res.reload} /> : !d ? <Skeleton rows={4} /> : (
        <>
          <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '6px 16px', margin: 0 }}>
            <dt className="muted">E-mail</dt><dd style={{ margin: 0 }}>{d.candidate.email}</dd>
            <dt className="muted">Telefone</dt><dd style={{ margin: 0 }}>{d.candidate.phone || '—'}</dd>
            <dt className="muted">Formação</dt><dd style={{ margin: 0 }}>{d.candidate.education || '—'}</dd>
            <dt className="muted">Habilidades</dt><dd style={{ margin: 0 }}>{d.candidate.skills || '—'}</dd>
            <dt className="muted">Consentimento</dt><dd style={{ margin: 0 }}>{d.candidate.consent ? 'Registrado' : 'Não registrado'}</dd>
          </dl>
          <h3>Candidaturas</h3>
          {d.applications.length === 0 ? <p className="muted">Nenhuma candidatura acessível para você.</p> : (
            <ul style={{ margin: 0, paddingLeft: 18 }}>{d.applications.map(a => <li key={a.id}>{a.job.title} — <Tag>{a.stage}</Tag> · fit {fitLabel(a.fit)} ({a.fit})</li>)}</ul>
          )}
        </>
      )}
      <footer><button className="btn" onClick={onClose}>Fechar</button></footer>
    </Modal>
  );
}
