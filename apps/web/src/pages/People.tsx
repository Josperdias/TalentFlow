import { useMemo, useState } from 'react';
import { api } from '../api/client';
import type { Employee } from '../api/types';
import { useResource } from '../state';
import { Empty, ErrorState, Field, PageHead, Skeleton, Tag } from '../components/ui';
import { fmtDate } from '../format';

export default function People() {
  const [q, setQ] = useState(''); const [dept, setDept] = useState('');
  const res = useResource<Employee[]>(s => api.get('/lifecycle/employees', s), [], ['employee', 'application']);
  const depts = useMemo(() => [...new Set((res.data ?? []).map(e => e.department))].sort(), [res.data]);
  const rows = (res.data ?? []).filter(e => (!dept || e.department === dept) && (!q || (e.name + e.job_title).toLowerCase().includes(q.toLowerCase())));
  return (
    <>
      <PageHead eyebrow="Pessoas" title="Colaboradores" lead="Quadro atual, com data de admissão e situação. Gestores veem apenas a própria equipe." />
      <div className="toolbar" role="search">
        <Field label="Buscar por nome ou cargo"><input value={q} onChange={e => setQ(e.target.value)} /></Field>
        <Field label="Área"><select value={dept} onChange={e => setDept(e.target.value)}><option value="">Todas</option>{depts.map(d => <option key={d}>{d}</option>)}</select></Field>
      </div>
      {res.error && !res.data ? <ErrorState error={res.error} onRetry={res.reload} /> : !res.data ? <Skeleton /> :
        !rows.length ? <Empty title="Nenhum colaborador encontrado" /> : (
          <div className="table-wrap">
            <table className="grid stack">
              <thead><tr><th>Matrícula</th><th>Nome</th><th>Cargo</th><th>Área</th><th>Admissão</th><th>Situação</th></tr></thead>
              <tbody>{rows.map(e => (
                <tr key={e.id}><td data-label="Matrícula" className="mono">{e.employee_code}</td><td data-label="Nome"><b style={{ fontWeight: 500 }}>{e.name}</b></td>
                  <td data-label="Cargo">{e.job_title || '—'}</td><td data-label="Área">{e.department}</td><td data-label="Admissão">{fmtDate(e.hire_date)}</td>
                  <td data-label="Situação"><Tag tone={e.status === 'active' ? 'positive' : ''}>{e.status === 'active' ? 'Ativo' : 'Desligado'}</Tag></td></tr>))}</tbody>
            </table>
          </div>
        )}
    </>
  );
}
