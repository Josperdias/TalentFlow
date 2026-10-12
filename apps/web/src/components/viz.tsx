import { useId, useMemo, useState, type ReactNode } from 'react';
import { Icon, type IconName } from './icons';
import { CountUp, useInView } from './motion';

const AVATAR = ['#5846D4', '#0B6B63', '#2A63A8', '#B0364B', '#8A5A12', '#3D4A7A'];
const initials = (name: string) => name.trim().split(/\s+/).slice(0, 2).map(p => p[0]?.toUpperCase() ?? '').join('') || '·';
const hue = (name: string) => AVATAR[[...name].reduce((a, c) => a + c.charCodeAt(0), 0) % AVATAR.length];

/** Iniciais sobre cor estável por nome. Decorativo: o nome sempre aparece em texto ao lado. */
export function Avatar({ name, size = 32 }: { name: string; size?: number }) {
  return <span className="avatar" aria-hidden="true" style={{ width: size, height: size, fontSize: size * 0.38, background: `linear-gradient(145deg, ${hue(name)}, color-mix(in srgb, ${hue(name)} 70%, #fff))` }}>{initials(name)}</span>;
}

/** Linha mínima de tendência (sem eixos), desenhada ao aparecer. Precisa de ao menos 2 pontos reais. */
export function Sparkline({ values, label }: { values: number[]; label: string }) {
  const gid = useId();
  if (values.length < 2) return null;
  const W = 120, H = 34, max = Math.max(1, ...values);
  const pts = values.map((v, i) => [(i / (values.length - 1)) * W, H - 3 - (v / max) * (H - 8)] as const);
  const line = pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  return (
    <svg className="spark" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label} preserveAspectRatio="none">
      <defs><linearGradient id={gid} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="currentColor" stopOpacity=".28" /><stop offset="1" stopColor="currentColor" stopOpacity="0" /></linearGradient></defs>
      <path d={`${line} L${W},${H} L0,${H} Z`} fill={`url(#${gid})`} className="spark-area" />
      <path d={line} pathLength={1} className="spark-line" />
    </svg>
  );
}

type KpiCount = { to: number; decimals?: number; suffix?: string };

/** Cartão de indicador: número que sobe, nota e (opcional) tendência real. `value` já vem tratado ("—" sem dado). */
export function Kpi({ label, value, count, note, icon, tone = 'brand', delay = 0, trend, trendLabel }: {
  label: string; value?: ReactNode; count?: KpiCount; note: ReactNode; icon: IconName; tone?: 'brand' | 'positive' | 'attention' | 'info'; delay?: number; trend?: number[]; trendLabel?: string;
}) {
  return (
    <div className={`kpi t-${tone}`} style={{ animationDelay: `${delay}ms` }}>
      <span className="kpi-ico"><Icon name={icon} size={18} /></span>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{count ? <CountUp to={count.to} decimals={count.decimals} suffix={count.suffix} /> : value}</div>
      <div className="kpi-note">{note}</div>
      {trend && trend.length > 1 && <Sparkline values={trend} label={trendLabel ?? `Tendência de ${label}`} />}
    </div>
  );
}

export interface Slice { label: string; value: number; color: string }

/** Rosca em SVG puro. Passar o mouse (ou focar) numa fatia destaca e mostra o valor no centro. Sem dados: anel vazio e "—". */
export function Donut({ slices, centerLabel }: { slices: Slice[]; centerLabel: string }) {
  const total = slices.reduce((a, s) => a + s.value, 0);
  const [hover, setHover] = useState<number | null>(null);
  const R = 52, C = 2 * Math.PI * R;
  let offset = 0;
  const active = hover == null ? null : slices[hover];
  return (
    <div className="donut">
      <svg viewBox="0 0 140 140" role="img" aria-label={total === 0 ? 'Sem candidaturas' : slices.map(s => `${s.label}: ${s.value}`).join(', ')}>
        <circle cx="70" cy="70" r={R} className="donut-track" />
        {total > 0 && slices.map((s, i) => {
          if (s.value <= 0) return null;
          const len = (s.value / total) * C;
          const el = <circle key={s.label} cx="70" cy="70" r={R} className={`donut-arc${hover === i ? ' on' : ''}${hover != null && hover !== i ? ' dim' : ''}`} stroke={s.color}
            strokeDasharray={`${Math.max(len - 3, 0)} ${C}`} strokeDashoffset={-offset} style={{ animationDelay: `${150 + i * 120}ms` }}
            tabIndex={0} aria-label={`${s.label}: ${s.value}`} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(i)} onBlur={() => setHover(null)} />;
          offset += len; return el;
        })}
      </svg>
      <div className="donut-center" aria-hidden="true"><b>{total === 0 ? '—' : active ? active.value : total}</b><span>{active ? active.label : centerLabel}</span></div>
    </div>
  );
}

const MONTH = new Intl.DateTimeFormat('pt-BR', { month: 'short' });
const MONTH_LONG = new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric' });
const monthDate = (ym: string) => { const [y, m] = ym.split('-').map(Number); return new Date(y, m - 1, 1); };

export interface SeriesPoint { month: string; applications: number; hired: number }

/** Gráfico de área/linha de dados reais por mês, com desenho animado e leitura ao passar o mouse (ou teclar ←/→). */
export function TrendChart({ points }: { points: SeriesPoint[] }) {
  const [ref, seen] = useInView<HTMLDivElement>();
  const gid = useId().replace(/:/g, '');
  const [idx, setIdx] = useState<number | null>(null);
  const W = 1000, H = 290, L = 44, R = 18, T = 16, B = 34;
  const geom = useMemo(() => {
    const maxRaw = Math.max(1, ...points.map(p => p.applications), ...points.map(p => p.hired));
    const step = maxRaw <= 5 ? 1 : maxRaw <= 12 ? 2 : maxRaw <= 30 ? 5 : maxRaw <= 80 ? 10 : 20;
    const max = Math.ceil(maxRaw / step) * step;
    const x = (i: number) => L + (points.length === 1 ? (W - L - R) / 2 : (i / (points.length - 1)) * (W - L - R));
    const y = (v: number) => T + (1 - v / max) * (H - T - B);
    const path = (key: 'applications' | 'hired') => points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p[key]).toFixed(1)}`).join(' ');
    const ticks = Array.from({ length: max / step + 1 }, (_, k) => k * step);
    return { max, x, y, path, ticks };
  }, [points]);
  if (points.length === 0) return <p className="muted">Sem candidaturas para montar a evolução.</p>;
  const a = geom.path('applications'), h = geom.path('hired');
  const last = points.length - 1;
  const area = `${a} L${geom.x(last).toFixed(1)},${H - B} L${geom.x(0).toFixed(1)},${H - B} Z`;
  const onMove = (e: React.MouseEvent<SVGRectElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const fx = ((e.clientX - r.left) / r.width) * (W - L - R);
    setIdx(Math.max(0, Math.min(last, Math.round((fx / (W - L - R)) * last))));
  };
  const cur = idx == null ? null : points[idx];
  const tipLeft = idx == null ? 0 : (geom.x(idx) / W) * 100;
  return (
    <div className={`trend${seen ? ' in' : ''}`} ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Candidaturas e contratações por mês: ${points.map(p => `${MONTH.format(monthDate(p.month))} ${p.applications} candidaturas, ${p.hired} contratações`).join('; ')}`}
        onMouseLeave={() => setIdx(null)} tabIndex={0}
        onKeyDown={e => { if (e.key === 'ArrowRight') setIdx(i => Math.min(last, (i ?? -1) + 1)); else if (e.key === 'ArrowLeft') setIdx(i => Math.max(0, (i ?? 1) - 1)); else if (e.key === 'Escape') setIdx(null); }} onBlur={() => setIdx(null)}>
        <defs>
          <linearGradient id={`a${gid}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--c-accent)" stopOpacity=".34" /><stop offset="1" stopColor="var(--c-accent)" stopOpacity="0" /></linearGradient>
          <linearGradient id={`l${gid}`} x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor="var(--c-brand)" /><stop offset="1" stopColor="var(--c-accent)" /></linearGradient>
        </defs>
        {geom.ticks.map(t => <g key={t}><line x1={L} x2={W - R} y1={geom.y(t)} y2={geom.y(t)} className="grid-line" /><text x={L - 8} y={geom.y(t) + 4} textAnchor="end" className="axis">{t}</text></g>)}
        {points.map((p, i) => (points.length <= 12 || i % 2 === 0) && <text key={p.month} x={geom.x(i)} y={H - 10} textAnchor="middle" className="axis">{MONTH.format(monthDate(p.month)).replace('.', '')}</text>)}
        <path d={area} fill={`url(#a${gid})`} className="t-area" />
        <path d={a} pathLength={1} stroke={`url(#l${gid})`} className="t-line" />
        <path d={h} pathLength={1} className="t-line hired" />
        {points.map((p, i) => <circle key={p.month} cx={geom.x(i)} cy={geom.y(p.applications)} r={idx === i ? 6 : 3.5} className="t-dot" style={{ animationDelay: `${700 + i * 50}ms` }} />)}
        {points.map((p, i) => p.hired > 0 && <circle key={`h${p.month}`} cx={geom.x(i)} cy={geom.y(p.hired)} r={idx === i ? 5.5 : 3} className="t-dot hired" style={{ animationDelay: `${800 + i * 50}ms` }} />)}
        {idx != null && <line x1={geom.x(idx)} x2={geom.x(idx)} y1={T} y2={H - B} className="cross" />}
        <rect x={L} y={T} width={W - L - R} height={H - T - B} fill="transparent" onMouseMove={onMove} />
      </svg>
      {cur && (
        <div className="tip" style={{ left: `${tipLeft}%` }} role="status">
          <b>{MONTH_LONG.format(monthDate(cur.month))}</b>
          <span><i className="sw a" />Candidaturas <strong>{cur.applications}</strong></span>
          <span><i className="sw h" />Contratações <strong>{cur.hired}</strong></span>
        </div>
      )}
      <div className="legend-inline"><span><i className="sw a" />Candidaturas por mês de inscrição</span><span><i className="sw h" />Contratações (mês do último movimento)</span></div>
    </div>
  );
}
