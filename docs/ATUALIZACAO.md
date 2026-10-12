# Atualização automática dos aplicativos (Windows e Android)

Objetivo: quando uma build nova é **publicada no GitHub**, os apps avisam e atualizam **dentro do próprio app, sem abrir o navegador**.

## Como funciona
```
GitHub Release publicada ──► SEU servidor (lê a Release, guarda o token, confere SHA-256) ──► app Windows / app Android
                                         (ou, sem GitHub: pasta infra/updates)
```
1. O app pergunta ao **seu servidor** (`GET /api/v1/client-updates/{windows|android}`) ao entrar, ao voltar para a tela e a cada poucas horas.
2. O servidor olha a **Release mais nova publicada** (rascunho é ignorado) e devolve versão, notas, tamanho e o SHA-256 (do arquivo `.sha256` da Release).
3. Se a versão for maior que a instalada, o app mostra **"Nova versão X disponível → Atualizar agora"**.
4. O app baixa **pelo seu servidor** (o token do GitHub nunca vai para o celular/PC), **confere o SHA-256** e instala:
   - **Windows:** executa o instalador em modo silencioso, que fecha o app, troca os arquivos, reabre e preserva dados e sessão.
   - **Android:** entrega o APK ao instalador do sistema (PackageInstaller). O Android mostra "Atualizar este aplicativo?" (você toca em
     Atualizar) e o app reabre quando você o abrir de novo. Na primeira vez o Android pede a permissão única "instalar apps desta fonte".

## O que você precisa configurar (uma vez)
No `.env` do servidor (veja `infra/.env.example`):
```
TF_UPDATES_GITHUB_REPO=Josperdias/TalentFlow
TF_UPDATES_GITHUB_TOKEN=            # só se o repositório for PRIVADO: token fino, somente leitura de "Contents" deste repositório
TF_UPDATES_PRERELEASES=true         # inclui versões -rc; use false para só versões finais
```
Depois `docker compose up -d`. O servidor precisa de saída para `api.github.com` e `github.com`.

**Publicar uma build:** atualize `VERSION`, crie a tag `vX.Y.Z` (o workflow `release` gera uma Release em **rascunho** com instalador `.exe`,
APK e os `.sha256`) e **publique** a Release no GitHub. Em até ~10 min (cache do servidor) os apps passam a oferecer a atualização.
Eu não publico Releases: essa é uma decisão sua.

**Sem GitHub:** copie `TalentFlow-Setup-vX.exe` + `windows.json` (e/ou `talentflow-android-vX.apk` + `android.json`) para `infra/updates/`
(os arquivos `windows.json`/`android.json` saem prontos do CI). A pasta tem prioridade sobre o GitHub.

## ANDROID: leia isto (limite do próprio Android)
O Android só aceita atualizar um app se o novo APK for **assinado com a mesma chave** do instalado. As builds de **depuração** que o CI
gera usam uma chave diferente a cada execução, então **a atualização dentro do app só funciona entre APKs de release assinados com a sua chave**.
Para ativar:
1. No seu computador: `keytool -genkeypair -v -keystore talentflow-release.jks -alias talentflow -keyalg RSA -keysize 4096 -validity 10000`
   (guarde o arquivo e as senhas num gerenciador de senhas; se perder, não dá mais para atualizar os apps instalados).
2. Cadastre os segredos `TF_KEYSTORE_BASE64`, `TF_KEYSTORE_PASSWORD`, `TF_KEY_ALIAS`, `TF_KEY_PASSWORD` no GitHub (veja `docs/GITHUB-CONFIGURACAO.md`).
3. Instale **uma vez** o APK de release assinado. Dali em diante o app atualiza sozinho. O servidor prefere o APK de release ao de depuração.
Se um build de depuração tentar atualizar, o Android recusa e o app mostra o motivo (não quebra nada).

## Segurança
- Exige login; o servidor só entrega o arquivo da versão mais nova; o app **recusa instalar** se o SHA-256 baixado não bater (testado).
- Download de **outro host** só com HTTPS e sem enviar o token. O token do GitHub fica só no servidor e não é repassado ao destino do download.
- **Limite honesto:** o instalador do Windows **não tem assinatura de código** (SmartScreen avisa "editor desconhecido" na instalação manual).
  A integridade vem do SHA-256 publicado na Release; quem controla o repositório ou o servidor controla o que os apps instalam.
  Com certificado de código, o próximo passo é assinar no CI e o app passar a exigir a assinatura.

## Linha de comando (implantação no Windows)
`TalentFlow-Setup-vX.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS` (por usuário) ou com `/ALLUSERS` (exige administrador).
`/RELAUNCH=1` reabre o app ao terminar. Desinstalar: `unins000.exe /VERYSILENT` na pasta do programa.

## O que foi testado
- **API (pytest, PostgreSQL):** login obrigatório; pasta própria (Windows e Android); GitHub simulado (rascunho ignorado, maior versão vence,
  pré-lançamento filtrável, SHA-256 lido do `.sha256`, download em streaming, só o arquivo da versão mais nova); SHA divergente; nome malicioso.
- **Núcleos C# e Kotlin:** precedência semântica (`rc.1 < rc.2 < rc.10 < final`), download + SHA-256, adulteração cancela e não deixa arquivo,
  host estrangeiro, servidor em subpasta. **Cadeia real** manifesto → download autenticado → SHA-256 contra a API real (local e CI).
- **CI (windows-latest):** instala silenciosamente, **atualiza por cima** (v99.0.0), confere versão no registro, DLL órfã removida, uma única
  entrada de desinstalação, desinstala.
- **Não testado:** clicar em "Atualizar agora" nos apps reais (Windows e Android só compilam no CI; nunca abri nenhum num aparelho/PC),
  o diálogo de instalação do Android, a atualização com o app aberto, a leitura de uma Release real do GitHub (só simulada), instalar "para todos os usuários".
