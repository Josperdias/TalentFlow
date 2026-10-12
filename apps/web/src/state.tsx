import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import * as client from './api/client';
import type { User } from './api/types';

// ---------- Sessão ----------
type AuthStatus = 'loading' | 'anon' | 'authed' | 'unreachable';
interface AuthCtx {
  user: User | null; status: AuthStatus; error: string;
  signIn: (email: string, password: string) => Promise<void>; signOut: () => Promise<void>; retry: () => void;
}
const Auth = createContext<AuthCtx>(null as never);
export const useAuth = () => useContext(Auth);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [error, setError] = useState('');
  const boot = useCallback(() => {
    setStatus('loading');
    client.restore().then(
      u => { setUser(u); setStatus(u ? 'authed' : 'anon'); },
      (e: Error) => { setError(e.message); setStatus('unreachable'); });
  }, []);
  useEffect(boot, [boot]);
  const value = useMemo<AuthCtx>(() => ({
    user, status, error, retry: boot,
    signIn: async (email, password) => { const u = await client.login(email, password); setUser(u); setStatus('authed'); },
    signOut: async () => { await client.logout().catch(() => undefined); setUser(null); setStatus('anon'); }
  }), [user, status, error, boot]);
  return <Auth.Provider value={value}>{children}</Auth.Provider>;
}

// ---------- Sincronização ----------
export type Connection = 'connecting' | 'online' | 'offline';
interface SyncCtx { connection: Connection; lastSync: Date | null; subscribe: (entities: string[], fn: () => void) => () => void; poke: () => void }
const Sync = createContext<SyncCtx>(null as never);
export const useSync = () => useContext(Sync);
const POLL_MS = 4000;

export function SyncProvider({ children, enabled = true }: { children: ReactNode; enabled?: boolean }) {
  const [connection, setConnection] = useState<Connection>(enabled ? 'connecting' : 'online');
  const [lastSync, setLast] = useState<Date | null>(null);
  const listeners = useRef(new Set<{ entities: string[]; fn: () => void }>());
  const cursor = useRef<number | null>(null);
  const timer = useRef<number>();

  const tick = useCallback(async () => {
    try {
      if (cursor.current === null) cursor.current = (await client.changesCursor()).cursor;
      const feed = await client.changes(cursor.current);
      cursor.current = feed.cursor;
      setConnection('online'); setLast(new Date());
      if (feed.entities.length) listeners.current.forEach(l => { if (l.entities.some(e => feed.entities.includes(e))) l.fn(); });
      if (feed.has_more) { timer.current = window.setTimeout(tick, 200); return; }
    } catch { setConnection('offline'); }
    timer.current = window.setTimeout(tick, POLL_MS);
  }, []);

  useEffect(() => {
    if (!enabled) return;
    tick();
    const visible = () => { if (!document.hidden) { window.clearTimeout(timer.current); tick(); } };
    document.addEventListener('visibilitychange', visible);
    window.addEventListener('online', visible);
    return () => { window.clearTimeout(timer.current); document.removeEventListener('visibilitychange', visible); window.removeEventListener('online', visible); };
  }, [tick, enabled]);

  const value = useMemo<SyncCtx>(() => ({
    connection, lastSync, poke: () => { window.clearTimeout(timer.current); tick(); },
    subscribe: (entities, fn) => { const l = { entities, fn }; listeners.current.add(l); return () => { listeners.current.delete(l); }; }
  }), [connection, lastSync, tick]);
  return <Sync.Provider value={value}>{children}</Sync.Provider>;
}

// ---------- Recursos ----------
export interface Resource<T> { data: T | null; error: client.ApiError | Error | null; loading: boolean; reload: () => void; stale: boolean }

/** Carrega dados e recarrega quando outro cliente altera as entidades observadas. */
export function useResource<T>(load: (signal: AbortSignal) => Promise<T>, deps: unknown[], entities: string[] = []): Resource<T> {
  const { subscribe } = useSync();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [stale, setStale] = useState(false);
  const [nonce, setNonce] = useState(0);
  const loadRef = useRef(load); loadRef.current = load;
  const key = entities.join(',');
  useEffect(() => {
    const ctl = new AbortController();
    setLoading(true);
    loadRef.current(ctl.signal).then(d => { setData(d); setError(null); setStale(false); }, e => { if ((e as Error).name !== 'AbortError') { setError(e); setStale(true); } })
      .finally(() => { if (!ctl.signal.aborted) setLoading(false); });
    return () => ctl.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);
  useEffect(() => (entities.length ? subscribe(entities, () => setNonce(n => n + 1)) : undefined),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [key, subscribe]);
  return { data, error, loading, stale, reload: () => setNonce(n => n + 1) };
}
