import { config } from '../config';
import type { Changes, User } from './types';

/** Erro de API com o status HTTP e a mensagem já em português vinda do servidor. */
export class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message);
  }
  /** 409 com `current` = o registro foi alterado em outro cliente. */
  get isConflict(): boolean { return this.status === 409; }
  get conflictSnapshot(): { current_version?: number; current?: unknown; message?: string } | null {
    const d = this.detail as { current_version?: number } | undefined;
    return this.status === 409 && d && typeof d === 'object' ? d : null;
  }
}

/** Falha de rede (servidor fora do ar, sem internet, CORS): nunca simulamos dados nesse caso. */
export class NetworkError extends Error {
  constructor() { super('Não foi possível falar com o servidor. Verifique a conexão e o endereço da API.'); }
}

type Mode = 'cookie' | 'bearer';
let csrf = '';
let access = '';
const REFRESH_KEY = 'tf.refresh';

export function authMode(): Mode {
  try {
    return new URL(config.apiBaseUrl, window.location.href).origin === window.location.origin ? 'cookie' : 'bearer';
  } catch { return 'cookie'; }
}

function url(path: string): string {
  return config.apiBaseUrl + (path.startsWith('/') ? path : '/' + path);
}

function readRefresh(): string { try { return sessionStorage.getItem(REFRESH_KEY) ?? ''; } catch { return ''; } }
function writeRefresh(v: string): void { try { v ? sessionStorage.setItem(REFRESH_KEY, v) : sessionStorage.removeItem(REFRESH_KEY); } catch { /* modo privado */ } }

interface Opts { body?: unknown; ifMatch?: number; signal?: AbortSignal; skipRefresh?: boolean }

async function raw(method: string, path: string, o: Opts): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (o.body !== undefined) headers['Content-Type'] = 'application/json';
  if (o.ifMatch !== undefined) headers['If-Match'] = String(o.ifMatch);
  if (authMode() === 'bearer' && access) headers.Authorization = 'Bearer ' + access;
  if (authMode() === 'cookie' && method !== 'GET' && csrf) headers['X-TF-CSRF'] = csrf;
  try {
    return await fetch(url(path), {
      method, headers, signal: o.signal, cache: 'no-store',
      credentials: authMode() === 'cookie' ? 'same-origin' : 'omit',
      body: o.body !== undefined ? JSON.stringify(o.body) : undefined
    });
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw e;
    throw new NetworkError();
  }
}

async function tryRefresh(): Promise<boolean> {
  const token = readRefresh();
  if (authMode() !== 'bearer' || !token) return false;
  const res = await raw('POST', '/auth/refresh', { body: { refresh_token: token }, skipRefresh: true });
  if (!res.ok) { access = ''; writeRefresh(''); return false; }
  const data = await res.json();
  access = data.access_token; writeRefresh(data.refresh_token);
  return true;
}

export async function request<T>(method: string, path: string, o: Opts = {}): Promise<T> {
  let res = await raw(method, path, o);
  if (res.status === 401 && !o.skipRefresh && (await tryRefresh())) res = await raw(method, path, o);
  const text = await res.text();
  let data: unknown = null;
  if (text) { try { data = JSON.parse(text); } catch { data = text; } }
  if (!res.ok) {
    const d = (data as { detail?: unknown } | null)?.detail;
    const message = typeof d === 'string' ? d : (d as { message?: string } | undefined)?.message
      ?? (Array.isArray(d) ? 'Revise os campos informados.' : `Erro ${res.status}`);
    throw new ApiError(res.status, message, d);
  }
  return data as T;
}

export const api = {
  get: <T>(p: string, signal?: AbortSignal) => request<T>('GET', p, { signal }),
  post: <T>(p: string, body?: unknown, ifMatch?: number) => request<T>('POST', p, { body: body ?? {}, ifMatch }),
  patch: <T>(p: string, body: unknown, ifMatch: number) => request<T>('PATCH', p, { body, ifMatch })
};

// ---- sessão ----
export async function login(email: string, password: string): Promise<User> {
  if (authMode() === 'cookie') {
    const data = await request<{ user: User; csrf: string }>('POST', '/auth/login', { body: { email, password }, skipRefresh: true });
    csrf = data.csrf;
    return data.user;
  }
  const data = await request<{ user: User; access_token: string; refresh_token: string }>(
    'POST', '/auth/token', { body: { email, password, client: 'web', device: navigator.userAgent.slice(0, 100) }, skipRefresh: true });
  access = data.access_token; writeRefresh(data.refresh_token);
  return data.user;
}

/** Restaura a sessão após recarregar a página; devolve null se não houver sessão válida. */
export async function restore(): Promise<User | null> {
  try {
    const data = await request<{ user: User }>('GET', '/me');
    if (authMode() === 'cookie') csrf = (await request<{ token: string }>('GET', '/auth/csrf')).token;
    return data.user;
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) return null;
    throw e;
  }
}

export async function logout(): Promise<void> {
  try { await request('POST', '/auth/logout', { body: {}, skipRefresh: true }); } finally { csrf = ''; access = ''; writeRefresh(''); }
}

export interface Health { status: string; api_version: string; min_client_version: Record<string, string> }
export const health = () => request<Health>('GET', '/health', { skipRefresh: true });
export const changes = (after: number, signal?: AbortSignal) => request<Changes>('GET', `/changes?after=${after}&limit=200`, { signal });
export const changesCursor = () => request<{ cursor: number }>('GET', '/changes/cursor');
