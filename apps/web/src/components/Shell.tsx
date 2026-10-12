import { NavLink, Outlet } from 'react-router-dom';
import { useAuth, useSync } from '../state';
import { ROLE_LABEL } from '../format';
import type { Role } from '../api/types';

const I = (d: string) => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={d} /></svg>;
const ICON = {
  home: I('M3 11l9-7 9 7M5 10v10h14V10'), jobs: I('M4 7h16v12H4zM9 7V4h6v3'), people: I('M16 11a4 4 0 10-8 0 4 4 0 008 0zM4 21c0-4 4-6 8-6s8 2 8 6'),
  team: I('M9 11a3 3 0 100-6 3 3 0 000 6zM3 20c0-3 3-5 6-5s6 2 6 5M17 11a3 3 0 100-6M21 20c0-2-1.5-3.600-4-4.300'),
  plan: I('M4 19V5M4 19h16M8 15l4-5 3 3 5-6'), leave: I('M5 5h14v15H5zM5 10h14M9 3v4M15 3v4'), account: I('M12 12a4 4 0 100-8 4 4 0 000 8zM5 21a7 7 0 0114 0')
};

interface Item { to: string; label: string; icon: keyof typeof ICON; roles: Role[]; group: string }
const ITEMS: Item[] = [
  { to: '/', label: 'Visão geral', icon: 'home', roles: ['admin', 'recruiter', 'manager', 'interviewer'], group: 'Trabalho' },
  { to: '/vagas', label: 'Vagas', icon: 'jobs', roles: ['admin', 'recruiter', 'manager', 'interviewer'], group: 'Recrutamento' },
  { to: '/candidatos', label: 'Candidatos', icon: 'people', roles: ['admin', 'recruiter', 'manager', 'interviewer'], group: 'Recrutamento' },
  { to: '/pessoas', label: 'Pessoas', icon: 'team', roles: ['admin', 'recruiter', 'manager'], group: 'Pessoas' },
  { to: '/desenvolvimento', label: 'Desenvolvimento', icon: 'plan', roles: ['admin', 'recruiter', 'manager'], group: 'Pessoas' },
  { to: '/ausencias', label: 'Ausências', icon: 'leave', roles: ['admin', 'recruiter', 'manager'], group: 'Pessoas' },
  { to: '/minhas-candidaturas', label: 'Candidaturas', icon: 'jobs', roles: ['candidate'], group: 'Trabalho' },
  { to: '/conta', label: 'Conta', icon: 'account', roles: ['admin', 'recruiter', 'manager', 'interviewer', 'candidate'], group: 'Conta' }
];

export function Mark({ size = 32 }: { size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="4" fill="#0B4F5C" /><path d="M7 9h18v4H18v12h-4V13H7z" fill="#fff" /><path d="M20 17h5v3h-5z" fill="#E0AE5B" /></svg>;
}

export default function Shell() {
  const { user } = useAuth();
  const { connection, lastSync, poke } = useSync();
  if (!user) return null;
  const items = ITEMS.filter(i => i.roles.includes(user.role));
  const groups = [...new Set(items.map(i => i.group))];
  const status = connection === 'online' ? `Sincronizado ${lastSync ? lastSync.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}` : connection === 'offline' ? 'Sem conexão com o servidor' : 'Conectando…';
  return (
    <div className="app">
      <a className="skip" href="#conteudo">Ir para o conteúdo</a>
      <aside className="rail">
        <div className="brand"><Mark /><div><b>TalentFlow</b><small>People</small></div></div>
        <nav className="nav" aria-label="Principal">
          {groups.map(g => (
            <div key={g}>
              <h2>{g}</h2>
              {items.filter(i => i.group === g).map(i => <NavLink key={i.to} to={i.to} end={i.to === '/'}>{ICON[i.icon]}<span>{i.label}</span></NavLink>)}
            </div>
          ))}
        </nav>
        <div className="rail-foot">
          <button className="conn btn quiet" style={{ justifyContent: 'flex-start', padding: 0, height: 'auto' }} onClick={poke} aria-live="polite" title="Verificar agora">
            <span className={`dot ${connection}`} /><span>{status}</span>
          </button>
          <div className="who"><b>{user.name}</b><span className="muted">{ROLE_LABEL[user.role]} · {user.company}</span></div>
        </div>
      </aside>
      <main id="conteudo" tabIndex={-1}>
        {connection === 'offline' && <div className="notice attention" role="status"><b>Sem conexão com o servidor</b>Os dados abaixo podem estar desatualizados e alterações não serão salvas até a conexão voltar.</div>}
        <Outlet />
      </main>
    </div>
  );
}
