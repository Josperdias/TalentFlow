import { useState } from 'react';
import { api } from '../api/client';
import type { SessionInfo } from '../api/types';
import { useAuth, useResource } from '../state';
import { ErrorState, PageHead, Skeleton, Tag } from '../components/ui';
import { fmtDateTime, ROLE_LABEL } from '../format';
import { config } from '../config';

export default function Account() {
  const { user, signOut } = useAuth();
  const res = useResource<SessionInfo[]>(s => api.get('/auth/sessions', s), []);
  const [msg, setMsg] = useState('');
  const revoke = async () => {
    const r = await api.post<{ revoked: number }>('/auth/sessions/revoke-others');
    setMsg(`${r.revoked} outra(s) sessão(ões) encerrada(s).`); res.reload();
  };
  return (
    <>
      <PageHead eyebrow="Conta" title={user?.name ?? ''} lead={`${user?.email} · ${user ? ROLE_LABEL[user.role] : ''} · ${user?.company}`}>
        <button className="btn" onClick={() => signOut()}>Sair</button>
      </PageHead>
      <section>
        <h2 className="eyebrow">Sessões ativas</h2>
        {res.error ? <ErrorState error={res.error} onRetry={res.reload} /> : !res.data ? <Skeleton rows={3} /> : (
          <div className="table-wrap"><table className="grid stack"><thead><tr><th>Cliente</th><th>Tipo</th><th>Expira</th><th /></tr></thead>
            <tbody>{res.data.map(s => <tr key={s.id}><td data-label="Cliente">{s.client}</td><td data-label="Tipo">{s.kind === 'cookie' ? 'Navegador' : 'Aplicativo'}</td><td data-label="Expira">{fmtDateTime(s.expires_at)}</td><td>{s.current && <Tag tone="info">Esta sessão</Tag>}</td></tr>)}</tbody></table></div>
        )}
        <div className="actions" style={{ marginTop: 12 }}><button className="btn" onClick={revoke}>Encerrar as outras sessões</button></div>
        <div aria-live="polite">{msg && <p className="muted" style={{ marginTop: 8 }}>{msg}</p>}</div>
      </section>
      {config.downloadsUrl && <section className="section"><h2 className="eyebrow">Aplicativos</h2><p>Instale o TalentFlow no <a href={config.downloadsUrl} rel="noopener noreferrer">Android e no Windows</a>. Os dois usam a mesma conta e os mesmos dados.</p></section>}
    </>
  );
}
