# Configurar o GitHub (passo a passo, ~10 minutos)

Tudo aqui é feito por você, no navegador, porque exige permissão de dono do repositório.
Nenhum segredo passa pelo chat nem entra no repositório.

## 1. Criar a branch `main`
Hoje só existe `ccr-8c6efdbd-nu48u7`. No GitHub: aba **Code** → seletor de branch → digite `main` → **Create branch**
(a partir da branch de trabalho, se quiser que `main` já contenha tudo; ou do commit-base `a47994e`).
Depois: **Settings → Branches → Default branch** → `main`.

## 2. Importar a proteção da `main` (arquivo JSON pronto)
**Settings → Rules → Rulesets → New ruleset → Import a ruleset** e escolha UM destes arquivos:

| Arquivo | Quando usar |
|---|---|
| `.github/rulesets/main.json` | Há outra pessoa/conta para aprovar. Exige 1 aprovação de code owner + testes. |
| `.github/rulesets/main-dono-sozinho.json` | Você é a única pessoa: o GitHub **não deixa o autor aprovar o próprio PR**, então este exige só os testes (e conversas resolvidas, squash, histórico linear). |

Os testes obrigatórios são os 4 jobs do workflow `ci` (policy, api, web, compose). Os workflows `android` e `windows` rodam só
quando `apps/android` ou `apps/windows` mudam, por isso não são "obrigatórios" (senão travariam PRs que não os tocam). Eles
continuam aparecendo no PR.

## 3. Habilitar auto-merge
**Settings → General → Pull Requests** → marque **Allow auto-merge** e **Automatically delete head branches**; deixe só **Allow squash merging**.
Depois crie o rótulo `automerge` (cor `0B4F5C`). Num PR com esse rótulo o workflow `auto-merge` liga o auto-merge do GitHub, que só conclui
com os testes verdes (e a aprovação, se usar `main.json`).

## 4. Segredos e variáveis (nomes em `.github/rulesets/segredos-e-variaveis.nomes.json`)
**Settings → Secrets and variables → Actions**
- Aba **Secrets** → *New repository secret*: `TF_KEYSTORE_BASE64`, `TF_KEYSTORE_PASSWORD`, `TF_KEY_ALIAS`, `TF_KEY_PASSWORD`.
- Aba **Variables** → *New repository variable*: `PUBLIC_WEB_URL` (o endereço do SEU site).

Gerar o keystore do Android (no seu computador; guarde o arquivo e as senhas num gerenciador de senhas — se perder, não dá para atualizar o app):

```bash
keytool -genkeypair -v -keystore talentflow-release.jks -alias talentflow -keyalg RSA -keysize 4096 -validity 10000
base64 -w0 talentflow-release.jks    # copie a saída para o segredo TF_KEYSTORE_BASE64
```

Com os 4 segredos, o job `apk` gera também o **APK de release assinado**. Sem eles gera só o de depuração.
Assinatura do instalador do Windows (certificado de código) **ainda não está no workflow**; precisa de um certificado e de um passo novo.

## 5. Liberar o merge para o Claude
Diga no chat: **"autorizo"** (ou "pode mesclar o PR N"). O Claude abre o PR em rascunho `ccr-8c6efdbd-nu48u7 → main`,
espera os testes e só mescla quando você confirmar. Release: sempre rascunho até você publicar.
