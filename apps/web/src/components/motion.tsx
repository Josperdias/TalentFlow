import { useEffect, useRef, useState } from 'react';

/** Respeita "reduzir movimento" do sistema: sem animações de valor nem de desenho. */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() => typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => {
    if (typeof matchMedia !== 'function') return;
    const m = matchMedia('(prefers-reduced-motion: reduce)');
    const on = () => setReduced(m.matches);
    m.addEventListener?.('change', on);
    return () => m.removeEventListener?.('change', on);
  }, []);
  return reduced;
}

const easeOut = (p: number) => 1 - Math.pow(1 - p, 3);

/** Número que sobe até o valor (e vai do valor antigo ao novo quando a sincronização traz mudança). O valor final fica sempre no texto para leitores de tela. */
export function CountUp({ to, decimals = 0, suffix = '', duration = 1100 }: { to: number; decimals?: number; suffix?: string; duration?: number }) {
  const reduced = useReducedMotion();
  const fmt = (n: number) => n.toLocaleString('pt-BR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + suffix;
  const [shown, setShown] = useState(reduced ? to : 0);
  const from = useRef(reduced ? to : 0);
  useEffect(() => {
    if (reduced) { setShown(to); from.current = to; return; }
    const a = from.current; const t0 = performance.now(); let raf = 0;
    const tick = (t: number) => {
      const p = Math.min(1, (t - t0) / duration); const v = a + (to - a) * easeOut(p);
      from.current = v; setShown(v);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to, reduced, duration]);
  return <><span className="sr-only">{fmt(to)}</span><span aria-hidden="true">{fmt(shown)}</span></>;
}

/** Marca o elemento como "visível" quando entra na tela (dispara animações de desenho uma única vez). */
export function useInView<T extends Element>(): [React.RefObject<T>, boolean] {
  const ref = useRef<T>(null);
  const [seen, setSeen] = useState(typeof IntersectionObserver === 'undefined');
  useEffect(() => {
    const el = ref.current;
    if (!el || seen) return;
    const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { setSeen(true); io.disconnect(); } }, { threshold: 0.2 });
    io.observe(el);
    return () => io.disconnect();
  }, [seen]);
  return [ref, seen];
}

/** Foco de luz que acompanha o ponteiro sobre cartões e painéis (CSS lê --mx/--my). Instalado uma vez no shell. */
export function usePointerSpotlight() {
  useEffect(() => {
    const on = (e: PointerEvent) => {
      const t = (e.target as Element | null)?.closest?.('.kpi, .panel, .card') as HTMLElement | null;
      if (!t) return;
      const r = t.getBoundingClientRect();
      t.style.setProperty('--mx', `${e.clientX - r.left}px`);
      t.style.setProperty('--my', `${e.clientY - r.top}px`);
    };
    document.addEventListener('pointermove', on, { passive: true });
    return () => document.removeEventListener('pointermove', on);
  }, []);
}

export type ThemeChoice = 'auto' | 'light' | 'dark';
const KEY = 'tf-theme';
function readTheme(): ThemeChoice { try { const v = localStorage.getItem(KEY); return v === 'light' || v === 'dark' ? v : 'auto'; } catch { return 'auto'; } }
function applyTheme(t: ThemeChoice) { const r = document.documentElement; if (t === 'auto') r.removeAttribute('data-theme'); else r.setAttribute('data-theme', t); }
applyTheme(readTheme());

/** Tema claro/escuro/automático, lembrado neste navegador (nunca é dado de negócio). */
export function useTheme(): [ThemeChoice, () => void] {
  const [theme, setTheme] = useState<ThemeChoice>(readTheme);
  const next = () => {
    const n: ThemeChoice = theme === 'auto' ? 'light' : theme === 'light' ? 'dark' : 'auto';
    setTheme(n); applyTheme(n);
    try { n === 'auto' ? localStorage.removeItem(KEY) : localStorage.setItem(KEY, n); } catch { /* sem armazenamento: vale só nesta sessão */ }
  };
  return [theme, next];
}
