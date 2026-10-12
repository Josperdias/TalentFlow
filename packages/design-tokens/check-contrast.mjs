// Confere pares de cores do design system contra a WCAG 2.1 AA. Uso: node packages/design-tokens/check-contrast.mjs
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const t = JSON.parse(readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), 'tokens.json'), 'utf8'));
const lin = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
const lum = h => { const n = parseInt(h.slice(1), 16); return 0.2126 * lin(n >> 16 & 255) + 0.7152 * lin(n >> 8 & 255) + 0.0722 * lin(n & 255); };
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
// [texto/elemento, fundo, mínimo]. 4.5 = texto normal; 3 = componente de interface/borda de controle.
const TEXT = [['ink', 'canvas'], ['ink', 'surface'], ['inkMuted', 'canvas'], ['inkMuted', 'surface'], ['inkMuted', 'sunken'],
  ['inkFaint', 'canvas'], ['inkFaint', 'surface'], ['inkFaint', 'sunken'], ['brand', 'surface'], ['brand', 'canvas'], ['brand', 'brandSoft'],
  ['onBrand', 'brand'], ['brandStrong', 'brandSoft'], ['attention', 'attentionSoft'], ['positive', 'positiveSoft'], ['critical', 'criticalSoft'],
  ['info', 'infoSoft'], ['attention', 'surface'], ['positive', 'surface'], ['critical', 'surface'], ['info', 'surface'],
  ['navInk', 'nav'], ['navMuted', 'nav'], ['navMuted', 'navRaised'], ['navActiveInk', 'navActive'], ['navInk', 'navRaised']];
const UI = [['lineStrong', 'surface'], ['lineStrong', 'canvas'], ['focus', 'surface'], ['focus', 'canvas']];
let bad = 0;
for (const mode of ['light', 'dark']) {
  const c = t.color[mode];
  for (const [list, min] of [[TEXT, 4.5], [UI, 3]]) for (const [fg, bg] of list) {
    const r = ratio(c[fg], c[bg]);
    if (r < min) { bad++; console.log(`FALHA ${mode}: ${fg} ${c[fg]} sobre ${bg} ${c[bg]} = ${r.toFixed(2)} (< ${min})`); }
  }
}
console.log(bad ? `${bad} par(es) abaixo do AA` : 'Contraste AA: todos os pares aprovados (claro e escuro)');
process.exit(bad ? 1 : 0);
