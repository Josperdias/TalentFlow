# Colocar o TalentFlow no ar de graça (máquina virtual da Oracle)

## Primeiro: o que precisa de servidor
O **site** é só HTML pronto, mas os **apps (Android e Windows)** e o próprio site precisam da **API + banco PostgreSQL**. Por isso
hospedagem só de HTML (GitHub Pages, por exemplo) **não basta**: ela não roda API nem banco. Você precisa de uma máquina que rode
Docker. Ela guarda os dados, serve o site, e entrega as atualizações dos apps.

## Opções gratuitas (resumo honesto; confira os limites atuais nos sites deles)
| Opção | Serve? | Observação |
|---|---|---|
| **Máquina virtual Oracle Cloud "Always Free"** (a que você tem) | **Sim, é a melhor** | Roda tudo (API, banco, site, atualizações). Prefira a **Ampere A1 (ARM)** — até 4 núcleos/24 GB somando; a AMD "Micro" tem só 1 GB e fica apertada. Cuidados: a Oracle pode recolher máquinas gratuitas ociosas por muito tempo e os limites mudam; **faça backup fora dela**. |
| GitHub Pages / Netlify / Vercel (só site) | Não sozinho | Só HTML. Faltaria API e banco. |
| Render, Fly.io, Railway, Koyeb (planos gratuitos) | Parcial | Costumam dormir, expirar o banco ou pedir cartão; mais peças para juntar (API aqui + banco ali). Só valem se a Oracle não servir. |
| Banco grátis (Neon/Supabase) + API em outro lugar | Parcial | Resolve o banco, não a API. Mais complexo que a Oracle. |

**Recomendação: Oracle (Ampere A1) + Docker + Caddy (HTTPS automático) + um subdomínio gratuito do DuckDNS.**

## Passo a passo
### 1. A máquina
1. Console Oracle → *Compute → Instances → Create*: imagem **Ubuntu 22.04/24.04**, forma **VM.Standard.A1.Flex** (2 OCPU / 12 GB é de sobra). Baixe a chave SSH.
2. **Abra as portas 80 e 443**: *Networking → Virtual Cloud Network → sua subnet → Security List → Add Ingress Rules* (origem `0.0.0.0/0`, TCP, portas 80 e 443).
3. **Libere também no firewall da própria máquina** (as imagens da Oracle bloqueiam por padrão):
   ```bash
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo apt-get install -y iptables-persistent && sudo netfilter-persistent save
   ```
4. Instale o Docker: `curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker $USER` (saia e entre de novo no SSH).

### 2. O endereço (domínio)
O HTTPS gratuito exige um nome. O jeito grátis mais simples: crie um subdomínio em **duckdns.org** (ex.: `meuhr.duckdns.org`) apontando para o
**IP público** da máquina. (Para um teste rápido, `SEU-IP-COM-TRACOS.sslip.io` também funciona, ex.: `203-0-113-5.sslip.io`.)
Eu não escolho nem registro domínio por você.

### 3. Subir o servidor
```bash
git clone https://github.com/Josperdias/TalentFlow.git && cd TalentFlow/infra
cp .env.example .env && nano .env
```
No `.env` preencha:
- `PGPASSWORD` = senha longa (`openssl rand -base64 32`)
- `SITE_ADDRESS` = `meuhr.duckdns.org` (sem https://)
- `TRUSTED_ORIGINS` = `https://meuhr.duckdns.org`
- `TF_UPDATES_GITHUB_REPO` = `Josperdias/TalentFlow` (para as atualizações automáticas dos apps)
- `TF_UPDATES_GITHUB_TOKEN` = só se o repositório for **privado** (token fino de leitura)

### 4. O site (ZIP compilado)
Na **primeira Release** (ou no artefato `talentflow-web` do CI) baixe `talentflow-web-vX.Y.Z.zip` e extraia dentro de `infra/site/`
(o `index.html` fica direto nessa pasta). O `config.json` já vem certo para "site e API no mesmo domínio".

### 5. Ligar tudo
```bash
docker compose -f docker-compose.yml -f docker-compose.caddy.yml up -d --build
docker compose logs -f api caddy      # espere "Application startup complete" e o certificado HTTPS ser emitido
```
### 6. Criar a empresa e o administrador
```bash
docker compose exec api python -m scripts.provision_admin --company "Minha Empresa" --slug minha-empresa --email voce@empresa.com.br
```
(a senha é pedida no terminal, mínimo 14 caracteres; produção não tem usuários de demonstração.)

### 7. Testar
1. Abra `https://meuhr.duckdns.org`, clique em **Diagnosticar conexão com a API** e entre.
2. No **Windows** e no **Android**, informe o endereço `meuhr.duckdns.org` na primeira tela e entre com o mesmo usuário.
3. Faça uma alteração no site e veja aparecer no app (a sincronização leva poucos segundos).

### 8. Backup (não pule)
`./backup.sh 14` gera um dump por dia (guarda 14). Agende no `cron` e **copie para fora da máquina** (outro provedor/seu PC). Os currículos ficam no volume `uploads`.

### 9. Primeira Release (para baixar os apps e ligar as atualizações)
1. Segredos do Android: veja `docs/GITHUB-CONFIGURACAO.md` (4 segredos). Sem eles o APK é só de teste e **não atualiza dentro do app**.
2. GitHub → *Actions → release → Run workflow* → tag `v1.3.0-rc.1` (precisa ser igual ao arquivo `VERSION`). Gera uma Release **em rascunho**.
3. Confira os arquivos e **publique** a Release. Daí em diante, cada versão nova publicada vira atualização nos apps (veja `docs/ATUALIZACAO.md`).

## O que NÃO foi testado
Eu não tenho Docker neste ambiente: a combinação `docker-compose.yml` + `docker-compose.caddy.yml`, o Caddyfile, a emissão do certificado,
as regras de firewall da Oracle e o DuckDNS **nunca foram executados por mim**. O que tem teste no CI: a API com PostgreSQL, o `docker compose`
base (subir, criar admin, login, backup e restauração) e o site. Se algo falhar, copie a mensagem de `docker compose logs` que eu corrijo.
