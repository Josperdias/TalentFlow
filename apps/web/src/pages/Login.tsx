import { useState, type FormEvent } from 'react';
import { useAuth } from '../state';
import { Mark } from '../components/Shell';
import { Field } from '../components/ui';
import { config } from '../config';
import { health } from '../api/client';

export default function Login() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState(''); const [password, setPassword] = useState('');
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const [diag, setDiag] = useState('');
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    try { await signIn(email, password); } catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  };
  const diagnose = async () => {
    setDiag('Verificando…');
    try { const h = await health(); setDiag(`API respondendo em ${config.apiBaseUrl} · versão ${h.api_version}`); }
    catch (e) { setDiag(`Falha ao acessar ${config.apiBaseUrl}: ${(e as Error).message}`); }
  };
  return (
    <div className="login">
      <section className="login-art" aria-hidden="false">
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}><Mark size={36} /><b style={{ font: '600 18px var(--f-display)' }}>TalentFlow People</b></div>
        <div><h1>Pessoas, da vaga à carreira, em um só registro.</h1><p>Recrutamento, jornada do colaborador e desenvolvimento no mesmo sistema, com os mesmos dados no site, no Android e no Windows.</p></div>
        <small>{config.apiBaseUrl}</small>
      </section>
      <section className="login-form">
        <form onSubmit={submit} aria-labelledby="login-h">
          <h1 id="login-h" style={{ fontSize: 24 }}>Entrar</h1>
          <Field label="E-mail"><input type="email" autoComplete="username" required value={email} onChange={e => setEmail(e.target.value)} /></Field>
          <Field label="Senha"><input type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} /></Field>
          {error && <div className="notice critical" role="alert">{error}</div>}
          <button className="btn primary" disabled={busy}>{busy ? 'Entrando…' : 'Entrar'}</button>
          <button type="button" className="btn quiet" onClick={diagnose}>Diagnosticar conexão com a API</button>
          {diag && <p className="muted" role="status" style={{ fontSize: 13 }}>{diag}</p>}
          {config.downloadsUrl && <p style={{ fontSize: 13 }}><a href={config.downloadsUrl} rel="noopener noreferrer">Baixar aplicativos Android e Windows</a></p>}
        </form>
      </section>
    </div>
  );
}
