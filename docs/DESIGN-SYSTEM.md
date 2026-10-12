# Design system "Ofício"

Software de RH corporativo com caráter editorial: **superfícies minerais, petróleo como marca, latão só para atenção**,
bordas finas no lugar de sombras, tabelas densas e números em serifa. Mesma linguagem nos três clientes, respeitando cada plataforma.

## O que evitamos de propósito
Grades de cartões coloridos, gradientes roxo/azul, cantos muito arredondados, sombras grandes, emojis decorativos, ilustrações stock,
microcopy repetitiva, "0" no lugar de "sem dados". O painel inicial é um **boletim** (livro-razão: rótulo, nota e número) + funil em barras.

## Tokens (fonte: `packages/design-tokens/tokens.json`)
- Cores (claro/escuro): `canvas`, `surface`, `sunken`, `line`, `lineStrong`, `ink`, `inkMuted`, `inkFaint`, `brand` (#0B4F5C),
  `brandStrong`, `brandSoft`, `onBrand`, `attention` (latão), `positive`, `critical`, `info` (+ variantes `*Soft`), `focus`.
- Espaço 4-8-12-16-24-32-48 px; raios 2/4/6 px; linha de tabela 36 px; alvo de toque 48 dp.
- Tipografia: títulos e números **Source Serif 4** (web) / serifa do sistema (Android, Georgia no Windows); interface **IBM Plex Sans**
  (web) / fonte do sistema (Android Roboto, Windows Segoe UI); rótulos e códigos em mono. Fontes web empacotadas no ZIP (OFL), sem CDN.
- Geração: `node packages/design-tokens/build.mjs` -> `tokens.css`, `Tokens.kt`, `Tokens.xaml`, `Tokens.cs`. O CI falha se houver deriva.

## Acessibilidade
- Contraste WCAG 2.1 AA **calculado** nos dois temas para todos os pares usados (texto >= 4,5:1; controles/linhas >= 3:1). Cinco pares
  falharam na primeira versão (`inkFaint`, `attention`, `lineStrong`) e foram corrigidos antes de usar.
- Foco visível, link "Ir para o conteúdo", `aria-live` em avisos, `<dialog>` nativo, rótulos em todos os campos, `prefers-reduced-motion`.
- **Não auditado** por ferramenta (axe/Lighthouse) nem por leitor de tela: ver `STATUS.md`.

## Padrões por plataforma
| | Navegação | Dados | Particularidades |
|---|---|---|---|
| Site | rail lateral (desktop) / barra inferior rolável (<=860 px) | tabelas densas -> listas empilhadas no celular | pipeline com seletor acessível + arrastar |
| Android | `NavigationBar` com 5 destinos; "Pessoas" agrupa 3 abas | cartões planos com borda fina | gesto "voltar" fecha o detalhe; sincroniza só com a tela visível |
| Windows | `NavigationView` à esquerda | tabelas com cabeçalho, pipeline em colunas | diálogos `ContentDialog`; Enter envia formulários |

Estados padronizados em todos: carregando, erro com "Tentar novamente", sem permissão, vazio, **dados desatualizados**, conflito de edição.
