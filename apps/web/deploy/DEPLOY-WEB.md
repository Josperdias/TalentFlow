# Publicar o site TalentFlow People no seu servidor

Este ZIP contém o site **já compilado**. Não é preciso instalar Node, nem compilar nada.
O site é só a "tela": os dados ficam na **API + PostgreSQL**, que você instala à parte
(veja `docs/DEPLOY-SERVIDOR.md` no repositório). O site, o app Android e o app Windows usam a mesma API.

## O que tem no pacote

| Arquivo | Para quê |
|---|---|
| `index.html`, `assets/` | O site. Os arquivos em `assets/` têm hash no nome (podem ficar em cache por muito tempo). |
| `config.json` | **Único arquivo que você edita.** Endereço da API e link de downloads. Sem senhas nem chaves. |
| `config.example.json` | Cópia de referência do `config.json`. |
| `nginx.conf.example`, `htaccess.example` | Exemplos de configuração do servidor (cabeçalhos de segurança, cache, proxy da API). |
| `VERSION` | Versão do pacote. |

## Passo a passo (recomendado: site e API no mesmo domínio)

1. **Extraia o ZIP** na pasta pública do site (ex.: `/var/www/talentflow` ou `public_html/`). Pode ser a raiz do domínio **ou uma subpasta** (`/talentflow/`): o site usa endereços com `#` (ex.: `/#/vagas`), então não exige regras de reescrita.
2. **Ligue o domínio à API.** No mesmo domínio, faça o servidor repassar `/api/` para o backend. Use `nginx.conf.example` (Nginx) ou `htaccess.example` (Apache). **Repasse o cabeçalho `Host` original** (`proxy_set_header Host $host;`), ou o login será bloqueado com "Origem inválida".
3. **Deixe o `config.json` assim** (padrão): `{ "apiBaseUrl": "/api/v1" }`.
4. **No servidor da API**, defina em `.env`: `COOKIE_SECURE=true` e `TRUSTED_ORIGINS=https://seu-dominio.com.br`.
5. **Use HTTPS.** Sem HTTPS o navegador não guardará o cookie de sessão seguro.
6. Abra o site. Na tela de login, **"Diagnosticar conexão com a API"** mostra se a API responde e em qual versão.

## Opção B — API em outro domínio ou servidor

Use quando a hospedagem do site (ex.: cPanel compartilhado) não consegue repassar `/api/`.

1. Em `config.json`, troque por `"apiBaseUrl": "https://api.seu-dominio.com.br/api/v1"`.
2. No `.env` da API: `CORS_ORIGINS=https://www.seu-dominio.com.br` (o endereço do site, sem barra final).
3. Nesse modo o site usa tokens (em memória + `sessionStorage`) em vez de cookie. É funcional, mas o cookie `HttpOnly` da opção recomendada é mais seguro contra XSS. Prefira a opção A quando possível.

## Botão de downloads

Preencha `"downloadsUrl"` com a página de Releases do repositório (APK e EXE). O link aparece na tela de login e em **Conta**.

## Atualizar para uma nova versão

Substitua `index.html` e a pasta `assets/` pelos novos (apague os `assets/` antigos). **Mantenha o seu `config.json`.**

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| "Origem inválida" ao entrar | O proxy não repassa o `Host`, ou falta `TRUSTED_ORIGINS` no `.env` da API. |
| "Não foi possível falar com o servidor" | API fora do ar, proxy `/api/` ausente, ou `apiBaseUrl` errado. Use o diagnóstico da tela de login. |
| Tela em branco | Arquivo `index.html` antigo com `assets/` novos (ou o contrário). Reenvie os dois. |
| Entra e volta ao login | Site em HTTP com `COOKIE_SECURE=true`. Use HTTPS. |
| Erro de CORS (opção B) | `CORS_ORIGINS` não contém exatamente o endereço do site. |

## O que NÃO foi validado

Os exemplos de Nginx e Apache **não foram testados no seu tipo de hospedagem**. O pacote foi validado com um
servidor estático de teste que aplica os mesmos cabeçalhos (incluindo a política CSP), um navegador Chromium,
a API e um PostgreSQL reais. Hospedagens que não permitem proxy reverso exigem a Opção B.
