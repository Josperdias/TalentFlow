import { useEffect, useRef, type ReactNode } from 'react';
import { ApiError, NetworkError } from '../api/client';

export function PageHead({ eyebrow, title, lead, children }: { eyebrow?: ReactNode; title: string; lead?: string; children?: ReactNode }) {
  return (
    <header className="page-head">
      <div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h1>{title}</h1>{lead && <p>{lead}</p>}</div>
      {children && <div className="actions">{children}</div>}
    </header>
  );
}

export const Tag = ({ tone = '', children }: { tone?: string; children: ReactNode }) => <span className={`tag ${tone}`}>{children}</span>;

export function Skeleton({ rows = 5 }: { rows?: number }) {
  return <div role="status" aria-label="Carregando" style={{ display: 'grid', gap: 12 }}>{Array.from({ length: rows }, (_, i) => <div key={i} className="skeleton" style={{ width: `${95 - (i % 3) * 14}%` }} />)}</div>;
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return <div className="empty"><b>{title}</b>{children}</div>;
}

/** Erro de rede, sem permissão ou do servidor: sempre com ação de tentar de novo. */
export function ErrorState({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  let title = 'Não foi possível carregar';
  let tone = 'critical';
  if (error instanceof NetworkError) title = 'Sem conexão com o servidor';
  else if (error instanceof ApiError && error.status === 403) { title = 'Sem permissão para ver esta área'; tone = 'attention'; }
  else if (error instanceof ApiError && error.status === 404) title = 'Registro não encontrado';
  return (
    <div className={`notice ${tone}`} role="alert">
      <b>{title}</b>
      <span>{error.message}</span>
      {onRetry && <div style={{ marginTop: 8 }}><button className="btn sm" onClick={onRetry}>Tentar novamente</button></div>}
    </div>
  );
}

export function Modal({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current; if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog ref={ref} onClose={onClose} onCancel={onClose} aria-labelledby="dlg-title">
      {open && <div className="dlg"><h2 id="dlg-title">{title}</h2>{children}</div>}
    </dialog>
  );
}

/** Mostrado quando outro cliente salvou antes (HTTP 409): nunca sobrescreve em silêncio. */
export function ConflictDialog({ open, message, onReload, onClose }: { open: boolean; message: string; onReload: () => void; onClose: () => void }) {
  return (
    <Modal open={open} onClose={onClose} title="Registro alterado por outra pessoa">
      <p>{message}</p>
      <p className="muted">Suas alterações não foram salvas. Carregue a versão atual, revise e aplique a edição novamente.</p>
      <footer>
        <button className="btn" onClick={onClose}>Fechar</button>
        <button className="btn primary" onClick={() => { onReload(); onClose(); }}>Carregar versão atual</button>
      </footer>
    </Modal>
  );
}

export const Field = ({ label, error, children }: { label: string; error?: string; children: ReactNode }) =>
  <label className="field"><span>{label}</span>{children}{error && <small role="alert">{error}</small>}</label>;
