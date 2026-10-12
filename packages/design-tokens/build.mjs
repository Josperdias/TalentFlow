// Gera tokens para os três clientes a partir de tokens.json. Uso: node packages/design-tokens/build.mjs
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../..');
const t = JSON.parse(readFileSync(resolve(here, 'tokens.json'), 'utf8'));
const kebab = s => s.replace(/[A-Z]/g, m => '-' + m.toLowerCase());
const pascal = s => s[0].toUpperCase() + s.slice(1);
const out = (rel, text) => { const p = resolve(root, rel); mkdirSync(dirname(p), { recursive: true }); writeFileSync(p, text); console.log('gerado', rel); };
const banner = 'GERADO por packages/design-tokens/build.mjs — não edite à mão.';

// ---- Web (CSS) ----
const vars = c => Object.entries(c).map(([k, v]) => `  --c-${kebab(k)}: ${v};`).join('\n');
const sp = Object.entries(t.space).map(([k, v]) => `  --s-${k}: ${v}px;`).join('\n');
const rd = Object.entries(t.radius).map(([k, v]) => `  --r-${k}: ${v}px;`).join('\n');
const fx = Object.entries(t.effects).map(([k, v]) => `  --${kebab(k)}: ${v};`).join('\n');
const mo = `  --m-fast: ${t.motion.fast}ms;\n  --m-base: ${t.motion.base}ms;\n  --m-slow: ${t.motion.slow}ms;\n  --ease: ${t.motion.ease};`;
const ty = Object.entries(t.type.scale).map(([k, v]) => `  --t-${kebab(k)}: ${v}px;`).join('\n');
out('apps/web/src/styles/tokens.css', `/* ${banner} */
:root {\n${vars(t.color.light)}\n${sp}\n${rd}\n${ty}\n${fx}\n${mo}
  --f-ui: ${t.type.web.ui};\n  --f-display: ${t.type.web.display};\n  --f-mono: ${t.type.web.mono};
  --rail-w: ${t.layout.railWidth}px;\n  --row-h: ${t.layout.rowHeight}px;\n  --content-max: ${t.layout.contentMax}px;
  color-scheme: light;\n}
@media (prefers-color-scheme: dark) {\n  :root:not([data-theme="light"]) {\n${vars(t.color.dark)}\n    color-scheme: dark;\n  }\n}
:root[data-theme="dark"] {\n${vars(t.color.dark)}\n  color-scheme: dark;\n}
`);

// ---- Android (Kotlin) ----
const argb = h => '0xFF' + h.slice(1).toUpperCase();
const kt = (name, c) => `    val ${name} = TfPalette(\n${Object.entries(c).map(([k, v]) => `        ${k} = Color(${argb(v)})`).join(',\n')}\n    )`;
out('apps/android/app/src/main/java/br/com/talentflow/people/ui/theme/Tokens.kt', `// ${banner}
package br.com.talentflow.people.ui.theme

import androidx.compose.ui.graphics.Color

data class TfPalette(
${Object.keys(t.color.light).map(k => `    val ${k}: Color`).join(',\n')}
)

object TfTokens {
${kt('Light', t.color.light)}

${kt('Dark', t.color.dark)}

    /** Espaçamentos em dp. */
    const val S1 = ${t.space['1']}; const val S2 = ${t.space['2']}; const val S3 = ${t.space['3']}; const val S4 = ${t.space['4']}
    const val S5 = ${t.space['5']}; const val S6 = ${t.space['6']}; const val S7 = ${t.space['7']}
    const val RADIUS_SM = ${t.radius.sm}; const val RADIUS_MD = ${t.radius.md}; const val RADIUS_LG = ${t.radius.lg}; const val RADIUS_XL = ${t.radius.xl}
    const val TOUCH_TARGET = ${t.layout.touchTarget}
}
`);

// ---- Windows (XAML ResourceDictionary) ----
const brush = (suffix, c) => Object.entries(c).map(([k, v]) => `    <Color x:Key="Tf${pascal(k)}Color${suffix}">${v.toUpperCase().replace('#', '#FF')}</Color>`).join('\n');
const themed = (name, c) => `  <ResourceDictionary x:Key="${name}">\n${brush('', c)}\n${Object.keys(c).map(k => `    <SolidColorBrush x:Key="Tf${pascal(k)}Brush" Color="{StaticResource Tf${pascal(k)}Color}" />`).join('\n')}\n  </ResourceDictionary>`;
out('apps/windows/TalentFlow.Windows/Styles/Tokens.xaml', `<!-- ${banner} -->
<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <ResourceDictionary.ThemeDictionaries>
${themed('Light', t.color.light)}
${themed('Dark', t.color.dark)}
  </ResourceDictionary.ThemeDictionaries>
  <x:Double x:Key="TfRowHeight">${t.layout.rowHeight}</x:Double>
  <x:Double x:Key="TfRailWidth">${t.layout.railWidth}</x:Double>
  <CornerRadius x:Key="TfRadiusMd">${t.radius.md}</CornerRadius>
  <CornerRadius x:Key="TfRadiusSm">${t.radius.sm}</CornerRadius>
  <CornerRadius x:Key="TfRadiusLg">${t.radius.lg}</CornerRadius>
  <CornerRadius x:Key="TfRadiusXl">${t.radius.xl}</CornerRadius>
</ResourceDictionary>
`);

// ---- Windows (C#): paleta para a interface construída em código ----
const cs = (name, c) => `    public static readonly IReadOnlyDictionary<string, Color> ${name} = new Dictionary<string, Color>\n    {\n${Object.entries(c).map(([k, v]) => `        ["${k}"] = Color.FromArgb(255, 0x${v.slice(1, 3)}, 0x${v.slice(3, 5)}, 0x${v.slice(5, 7)})`).join(',\n')}\n    };`;
out('apps/windows/TalentFlow.Windows/Styles/Tokens.cs', `// ${banner}
using Windows.UI;

namespace TalentFlow.Windows.Styles;

public static class TfTokens
{
${cs('Light', t.color.light)}

${cs('Dark', t.color.dark)}

    public const double RowHeight = ${t.layout.rowHeight};
    public const double RailWidth = ${t.layout.railWidth};
    public const double RadiusSm = ${t.radius.sm};
    public const double RadiusMd = ${t.radius.md};
    public const double RadiusLg = ${t.radius.lg};
    public const double RadiusXl = ${t.radius.xl};
}
`);
