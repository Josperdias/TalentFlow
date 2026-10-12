import { useLayoutEffect, useRef } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth, useSync } from '../state';
import { ROLE_LABEL } from '../format';
import type { Role } from '../api/types';
import { Icon, type IconName } from './icons';
import { Avatar } from './viz';
import { usePointerSpotlight, useTheme } from './motion';

interface Item { to: string; label: string; icon: IconName; roles: Role[]; group: string }
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

/** Marca: tile em gradiente com o fluxo (três nós ligados). */
export function Mark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
      <defs><linearGradient id="tf-mark" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#6C58F0" /><stop offset=".6" stopColor="#8B6CF0" /><stop offset="1" stopColor="#B27BF5" /></linearGradient></defs>
      <rect width="40" height="40" rx="12" fill="url(#tf-mark)" />
      <path d="M11 12h18M20 12v16" stroke="#fff" strokeWidth="3.6" strokeLinecap="round" />
      <circle cx="29" cy="28" r="3.2" fill="#fff" opacity=".92" /><circle cx="11" cy="28" r="2.2" fill="#fff" opacity=".55" />
    </svg>
  );
}

function crumb(pathname: string, items: Item[]) {
  if (pathname.startsWith('/vagas/')) return 'Vagas · Detalhe';
  const hit = [...items].reverse().find(i => (i.to === '/' ? pathname === '/' : pathname.startsWith(i.to)));
  return hit?.label ?? 'TalentFlow';
}

export default function Shell() {
  const { user } = useAuth();
  const { connection, lastSync, poke } = useSync();
  const { pathname } = useLocation();
  const [theme, cycleTheme] = useTheme();
  const nav = useRef<HTMLElement>(null);
  usePointerSpotlight();
  // Pílula de seleção que desliza até o item ativo (posição medida; no celular desliza na horizontal).
  useLayoutEffect(() => {
    const n = nav.current; if (!n) return;
    const place = () => {
      const a = n.querySelector<HTMLElement>('a[aria-current="page"]');
      if (!a) { n.style.setProperty('--pill-o', '0'); return; }
      n.style.setProperty('--pill-y', `${a.offsetTop}px`); n.style.setProperty('--pill-h', `${a.offsetHeight}px`);
      n.style.setProperty('--pill-x', `${a.offsetLeft}px`); n.style.setProperty('--pill-w', `${a.offsetWidth}px`); n.style.setProperty('--pill-o', '1');
    };
    place(); addEventListener('resize', place);
    return () => removeEventListener('resize', place);
  }, [pathname, user?.role]);
  if (!user) return null;
  const items = ITEMS.filter(i => i.roles.includes(user.role));
  const groups = [...new Set(items.map(i => i.group))];
  const status = connection === 'online' ? `Sincronizado ${lastSync ? lastSync.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}` : connection === 'offline' ? 'Sem conexão com o servidor' : 'Conectando…';
  return (
    <div className="app">
      <a className="skip" href="#conteudo">Ir para o conteúdo</a>
      <aside className="rail">
        <div className="brand"><Mark size={38} /><div><b>TalentFlow</b><small>People</small></div></div>
        <nav className="nav" aria-label="Principal" ref={nav}>
          <span className="nav-pill" aria-hidden="true" />
          {groups.map(g => (
            <div key={g}>
              <h2>{g}</h2>
              {items.filter(i => i.group === g).map(i => <NavLink key={i.to} to={i.to} end={i.to === '/'}><Icon name={i.icon} /><span>{i.label}</span></NavLink>)}
            </div>
          ))}
        </nav>
        <div className="rail-foot">
          <div className="who"><Avatar name={user.name} size={36} /><div><b>{user.name}</b><span>{ROLE_LABEL[user.role]}</span></div></div>
        </div>
      </aside>
      <div className="stage">
        <header className="topbar">
          <div className="crumb" aria-hidden="true"><span>{user.company}</span><i>/</i><b>{crumb(pathname, items)}</b></div>
          <div className="top-actions">
          <button className="chip theme" onClick={cycleTheme} title={`Tema: ${theme === 'auto' ? 'automático' : theme === 'light' ? 'claro' : 'escuro'} (clique para alternar)`} aria-label={`Tema: ${theme === 'auto' ? 'automático' : theme === 'light' ? 'claro' : 'escuro'}. Alternar`}>
            <Icon name={theme === 'dark' ? 'moon' : theme === 'light' ? 'sun' : 'auto'} size={16} /><span>{theme === 'auto' ? 'Auto' : theme === 'light' ? 'Claro' : 'Escuro'}</span>
          </button>
          <button className={`chip conn ${connection}`} onClick={poke} aria-live="polite" title="Verificar agora"><span className={`dot ${connection}`} /><span>{status}</span></button>
          </div>
        </header>
        <main id="conteudo" tabIndex={-1}>
          {connection === 'offline' && <div className="notice attention" role="status"><b>Sem conexão com o servidor</b>Os dados abaixo podem estar desatualizados e alterações não serão salvas até a conexão voltar.</div>}
          <div key={pathname} className="route"><Outlet /></div>
        </main>
      </div>
    </div>
  );
}
