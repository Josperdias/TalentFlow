import { useState, type FormEvent } from 'react';
import { useAuth } from '../state';
import { Mark } from '../components/Shell';
import { Icon } from '../components/icons';
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
      <section className="login-art">
        <span className="orb o1" aria-hidden="true" /><span className="orb o2" aria-hidden="true" /><span className="grid-bg" aria-hidden="true" />
        <div className="login-brand"><Mark size={42} /><b>TalentFlow <small>People</small></b></div>
        <div className="login-copy">
          <p className="kicker">Recrutamento · Pessoas · Desenvolvimento</p>
          <h1>Pessoas, da vaga à carreira, em um só registro.</h1>
          <p className="lede">Os mesmos dados no site, no Android e no Windows: o que uma pessoa altera aparece para as outras em segundos.</p>
          <ul className="points">
            <li><Icon name="sync" size={18} /><span>Sincronização entre todos os aplicativos</span></li>
            <li><Icon name="shield" size={18} /><span>Permissões e dados separados por empresa</span></li>
            <li><Icon name="check" size={18} /><span>Conflitos de edição nunca sobrescrevem em silêncio</span></li>
          </ul>
        </div>
        <small className="login-foot">{config.apiBaseUrl}</small>
      </section>
      <section className="login-form">
        <form onSubmit={submit} aria-labelledby="login-h">
          <h1 id="login-h">Entrar</h1>
          <p className="muted">Use o e-mail e a senha da sua conta.</p>
          <Field label="E-mail"><input type="email" autoComplete="username" required value={email} onChange={e => setEmail(e.target.value)} /></Field>
          <Field label="Senha"><input type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} /></Field>
          {error && <div className="notice critical" role="alert">{error}</div>}
          <button className="btn primary lg" disabled={busy}>{busy ? 'Entrando…' : 'Entrar'}</button>
          <button type="button" className="btn quiet" onClick={diagnose}>Diagnosticar conexão com a API</button>
          {diag && <p className="muted" role="status" style={{ fontSize: 13 }}>{diag}</p>}
          {config.downloadsUrl && <p style={{ fontSize: 13 }}><a href={config.downloadsUrl} rel="noopener noreferrer">Baixar aplicativos Android e Windows</a></p>}
        </form>
      </section>
    </div>
  );
}
