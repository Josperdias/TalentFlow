const dateFmt = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' });
const dateTimeFmt = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
const money = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });

export const fmtDate = (v?: string | null) => { if (!v) return '—'; const d = new Date(v.length === 10 ? v + 'T00:00:00' : v); return isNaN(+d) ? '—' : dateFmt.format(d); };
export const fmtDateTime = (v?: string | null) => { if (!v) return '—'; const d = new Date(v); return isNaN(+d) ? '—' : dateTimeFmt.format(d); };
export const fmtMoney = (n: number) => (n > 0 ? money.format(n) : '—');
export const today = () => new Date().toISOString().slice(0, 10);

export const JOB_STATUS: Record<string, { label: string; tone: string }> = {
  open: { label: 'Aberta', tone: 'positive' }, approval: { label: 'Em aprovação', tone: 'attention' },
  closed: { label: 'Encerrada', tone: '' }, archived: { label: 'Arquivada', tone: '' }
};
export const LEAVE_STATUS: Record<string, { label: string; tone: string }> = {
  pending: { label: 'Pendente', tone: 'attention' }, approved: { label: 'Aprovada', tone: 'positive' }, rejected: { label: 'Recusada', tone: 'critical' }
};
export const LEAVE_KIND: Record<string, string> = { vacation: 'Férias', personal: 'Pessoal', medical: 'Saúde', other: 'Outro' };
export const ROLE_LABEL: Record<string, string> = {
  admin: 'Administração', recruiter: 'Recrutamento', manager: 'Gestão', interviewer: 'Entrevistas', candidate: 'Candidatura'
};
export const fitLabel = (n: number) => (n >= 75 ? 'Alto' : n >= 50 ? 'Médio' : 'Baixo');
