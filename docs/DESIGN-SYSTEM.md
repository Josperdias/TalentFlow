# Design system "Aurora"

Software de RH corporativo premium, na linguagem do protótipo original (navy profundo + violeta), com acabamento mais cuidadoso:
**menu lateral escuro em gradiente, superfícies claras e frias, cantos generosos (10-20 px), sombras suaves, indicadores em cartões
com cor de significado, gráficos em SVG próprio e movimento discreto**. Mesma linguagem nos três clientes, respeitando cada plataforma.
(A primeira versão, "Ofício", era mais austera e foi substituída a pedido: ver `docs/STATUS.md`.)

## Regras de gosto
- Gradiente só em decoração (marca, barras, fundo do login) e em botões primários **com contraste AA garantido** (`gradAction`).
  Nunca atrás de texto pequeno em cor clara.
- Cor tem significado: violeta = marca/ação, verde = positivo, âmbar = atenção, vermelho = crítico, azul = informação.
- Números grandes em Plus Jakarta Sans 700 (tabulares); títulos e marca em **Fraunces** (serifa de display, variável).
- "Sem dado" é `—`, nunca `0`. Nenhum gráfico inventa série: o que não existe na API não é desenhado (não há "evolução 12 meses").
- Movimento: entrada em cascata dos cartões, barras e rosca que crescem, elevação ao passar o mouse, diálogos com "pop",
  pulso no indicador de conexão. Tudo some com `prefers-reduced-motion`.

## Tokens (fonte: `packages/design-tokens/tokens.json`)
- Cores (claro/escuro): `canvas`, `surface`, `sunken`, `line`, `lineStrong`, `ink`, `inkMuted`, `inkFaint`, `brand` (#5846D4), `brandStrong`,
  `brandSoft`, `onBrand`, `accent`, `attention`, `positive`, `critical`, `info` (+ `*Soft`), `focus`, e o grupo do menu: `nav`, `navRaised`,
  `navInk`, `navMuted`, `navLine`, `navActive`, `navActiveInk`.
- Espaço 4-8-12-16-24-32-48; raios 6/10/14/20; linha de tabela 44; alvo de toque 48 dp. Efeitos: `shadowSm/Md/Lg`, `gradBrand`, `gradNav`,
  `gradHero`, `gradAction`. Movimento: 120/220/520 ms, `cubic-bezier(.2,.8,.2,1)`.
- Tipografia: **Plus Jakarta Sans** (interface) e **Fraunces** (títulos/marca), ambas OFL, empacotadas no ZIP do site (sem CDN).
- Geração: `node packages/design-tokens/build.mjs` -> `tokens.css`, `Tokens.kt`, `Tokens.xaml`, `Tokens.cs`.
  Contraste: `node packages/design-tokens/check-contrast.mjs` (falha se algum par ficar abaixo do AA).

## Acessibilidade
- Contraste WCAG 2.1 AA **calculado** nos dois temas para todos os pares usados (texto >= 4,5:1; controles/linhas >= 3:1). `check-contrast.mjs` cobre 30 pares por tema
  (texto >= 4,5; controles >= 3), incluindo o menu escuro e o texto branco sobre o gradiente do botão.
- Foco visível, link "Ir para o conteúdo", `aria-live` em avisos, `<dialog>` nativo, rótulos em todos os campos, `prefers-reduced-motion`.
- **Não auditado** por ferramenta (axe/Lighthouse) nem por leitor de tela: ver `STATUS.md`.

## Padrões por plataforma
| | Navegação | Dados | Particularidades |
|---|---|---|---|
| Site | menu lateral escuro + barra superior com migalha e estado de sincronização (desktop) / barra inferior flutuante rolável (<=860 px) | cartões de indicador, funil, rosca; tabelas -> listas empilhadas no celular | pipeline com seletor acessível + arrastar |
| Android | `NavigationBar` com 5 destinos; "Pessoas" agrupa 3 abas | cartões arredondados | gesto "voltar" fecha o detalhe; sincroniza só com a tela visível |
| Windows | `NavigationView` à esquerda | tabelas com cabeçalho, pipeline em colunas | diálogos `ContentDialog`; Enter envia formulários |

Estados padronizados em todos: carregando, erro com "Tentar novamente", sem permissão, vazio, **dados desatualizados**, conflito de edição.
