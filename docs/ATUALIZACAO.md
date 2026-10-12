# Instalador do Windows e atualização dos aplicativos

## O que existe
- **`TalentFlow-Setup-vX.Y.Z.exe`** (Inno Setup, gerado pelo CI): instala **e atualiza**. O `AppId` é fixo, então rodar um instalador mais
  novo por cima atualiza no lugar: fecha o aplicativo, troca os arquivos (remove DLLs da versão anterior), reabre e **preserva dados e
  sessão** (ficam em `%LOCALAPPDATA%\TalentFlow`, fora da pasta do programa). Instala por usuário, sem administrador (pode escolher "para todos").
- **Atualização dentro do app:** ao entrar (e a cada 6 h) o app pergunta ao SEU servidor se há versão mais nova. Se houver, aparece uma
  barra "Nova versão X disponível" com **Atualizar agora**: baixa, confere o SHA-256, executa o instalador em modo silencioso e reabre.
  Em *Conta → Verificar atualizações* dá para forçar a checagem.
- **Pacote portátil (.zip)**: sem instalador, sem atualização automática.

## Como publicar uma atualização no seu servidor
1. Gere a versão: atualize `VERSION`, abra o PR, deixe o CI passar e baixe o artefato `talentflow-windows` (ou a Release em rascunho).
2. Copie **dois arquivos** para a pasta de atualizações do servidor (`infra/updates/`, montada em `/updates` no contêiner):
   `TalentFlow-Setup-vX.Y.Z.exe` e `windows.json` (o CI gera os dois).
3. Pronto: não precisa reiniciar. Em até 6 h (ou ao reabrir o app) as máquinas avisam.

`windows.json`: `{"version":"1.4.0","file":"TalentFlow-Setup-v1.4.0.exe","sha256":"<64 hex>","notes":"o que mudou"}`

## Segurança (leia)
- O servidor só entrega o arquivo citado no manifesto, **exige login** e recusa se o SHA-256 real do arquivo não bater com o manifesto.
- O app recusa executar se o SHA-256 baixado não bater (testado). Download de **outro host** só com HTTPS e sem enviar o token.
- **Limite honesto:** o instalador **não tem assinatura de código** (sem certificado). A integridade vem do SHA-256 publicado pelo SEU
  servidor via HTTPS; quem controlar o servidor controla o que os apps instalam. O Windows SmartScreen avisará "editor desconhecido" na
  instalação manual. Com certificado de código, o próximo passo é assinar no CI e o app passar a exigir a assinatura.
- Sem `TF_UPDATES_DIR`/manifesto, nada é oferecido e o app funciona normalmente.

## Linha de comando (implantação em várias máquinas)
`TalentFlow-Setup-vX.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS` (por usuário) ou com `/ALLUSERS` (exige administrador).
`/RELAUNCH=1` reabre o app ao terminar. Desinstalar: `unins000.exe /VERYSILENT` na pasta do programa.

## O que foi testado
- API (pytest, PostgreSQL): login obrigatório, manifesto, download, SHA-256 divergente, nome de arquivo malicioso.
- Core C# (xUnit): precedência semântica (`1.3.0-rc.1 < rc.2 < 1.3.0`), download + SHA-256, adulteração cancela e não deixa arquivo,
  host estrangeiro, servidor em subpasta. **Cadeia real** manifesto -> download autenticado -> SHA-256 contra a API real (local e CI).
- CI (windows-latest): instala silenciosamente, **atualiza por cima** (versão 99.0.0), confere versão no registro, DLL órfã removida,
  uma única entrada de desinstalação, e desinstala.
- **Não testado:** clicar em "Atualizar agora" no app real (a interface só compila no CI), atualização com o app aberto em máquina real,
  instalação "para todos os usuários", Android (atualização do APK é manual por enquanto).
