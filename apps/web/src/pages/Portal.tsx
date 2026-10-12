import { api } from '../api/client';
import { useResource } from '../state';
import { Empty, ErrorState, PageHead, Skeleton, Tag } from '../components/ui';
import { fmtDate, fmtDateTime } from '../format';

interface Row { id: number; job: string; company: string; stage: string; status: string; applied_at: string; interviews: { id: number; starts_at: string; status: string }[]; offers: { status: string }[] }

export default function Portal() {
  const res = useResource<{ applications: Row[] }>(s => api.get('/portal', s), []);
  return (
    <>
      <PageHead eyebrow="Candidatura" title="Minhas candidaturas" lead="Acompanhe em que etapa está cada processo seletivo." />
      {res.error && !res.data ? <ErrorState error={res.error} onRetry={res.reload} /> : !res.data ? <Skeleton /> :
        !res.data.applications.length ? <Empty title="Nenhuma candidatura encontrada">Candidaturas feitas com este e-mail aparecem aqui.</Empty> : (
          <div className="table-wrap"><table className="grid stack"><thead><tr><th>Vaga</th><th>Empresa</th><th>Etapa</th><th>Candidatura</th><th>Entrevistas</th></tr></thead>
            <tbody>{res.data.applications.map(a => <tr key={a.id}><td data-label="Vaga">{a.job}</td><td data-label="Empresa">{a.company}</td><td data-label="Etapa"><Tag>{a.stage}</Tag></td>
              <td data-label="Candidatura">{fmtDate(a.applied_at)}</td><td data-label="Entrevistas">{a.interviews.length ? a.interviews.map(i => fmtDateTime(i.starts_at)).join(', ') : '—'}</td></tr>)}</tbody></table></div>
        )}
    </>
  );
}
