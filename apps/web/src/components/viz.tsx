import type { ReactNode } from 'react';
import { Icon, type IconName } from './icons';

const AVATAR = ['#5846D4', '#0B6B63', '#2A63A8', '#B0364B', '#8A5A12', '#3D4A7A'];
const initials = (name: string) => name.trim().split(/\s+/).slice(0, 2).map(p => p[0]?.toUpperCase() ?? '').join('') || '·';
const hue = (name: string) => AVATAR[[...name].reduce((a, c) => a + c.charCodeAt(0), 0) % AVATAR.length];

/** Iniciais sobre cor estável por nome. Decorativo: o nome sempre aparece em texto ao lado. */
export function Avatar({ name, size = 32 }: { name: string; size?: number }) {
  return <span className="avatar" aria-hidden="true" style={{ width: size, height: size, fontSize: size * 0.38, background: `linear-gradient(145deg, ${hue(name)}, color-mix(in srgb, ${hue(name)} 70%, #fff))` }}>{initials(name)}</span>;
}

/** Cartão de indicador. `value` já vem tratado (— quando não há dado). */
export function Kpi({ label, value, note, icon, tone = 'brand', delay = 0 }: { label: string; value: ReactNode; note: ReactNode; icon: IconName; tone?: 'brand' | 'positive' | 'attention' | 'info'; delay?: number }) {
  return (
    <div className={`kpi t-${tone}`} style={{ animationDelay: `${delay}ms` }}>
      <span className="kpi-ico"><Icon name={icon} size={18} /></span>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-note">{note}</div>
    </div>
  );
}

export interface Slice { label: string; value: number; color: string }

/** Rosca em SVG puro (sem biblioteca). Sem dados: anel vazio e "—". */
export function Donut({ slices, centerLabel }: { slices: Slice[]; centerLabel: string }) {
  const total = slices.reduce((a, s) => a + s.value, 0);
  const R = 52, C = 2 * Math.PI * R;
  let offset = 0;
  return (
    <div className="donut">
      <svg viewBox="0 0 140 140" role="img" aria-label={total === 0 ? 'Sem candidaturas' : slices.map(s => `${s.label}: ${s.value}`).join(', ')}>
        <circle cx="70" cy="70" r={R} className="donut-track" />
        {total > 0 && slices.filter(s => s.value > 0).map((s, i) => {
          const len = (s.value / total) * C;
          const el = <circle key={s.label} cx="70" cy="70" r={R} className="donut-arc" stroke={s.color} strokeDasharray={`${Math.max(len - 3, 0)} ${C}`} strokeDashoffset={-offset} style={{ animationDelay: `${150 + i * 120}ms` }} />;
          offset += len; return el;
        })}
      </svg>
      <div className="donut-center"><b>{total === 0 ? '—' : total}</b><span>{centerLabel}</span></div>
    </div>
  );
}
