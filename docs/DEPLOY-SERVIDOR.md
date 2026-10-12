# Instalar o servidor (API + PostgreSQL)

Requisitos: um servidor Linux com Docker e Docker Compose, um domínio e HTTPS (ex.: Nginx + Let's Encrypt).
O site (ZIP) e os aplicativos usam **este mesmo servidor**. Nada aqui foi publicado por nós: você escolhe o domínio.

## 1. Configurar
```bash
git clone <seu-repositorio> talentflow && cd talentflow/infra
cp .env.example .env        # edite: PGPASSWORD (senha longa), TRUSTED_ORIGINS=https://rh.suaempresa.com.br
docker compose up -d --build   # sobe PostgreSQL e a API; as migrações rodam sozinhas
docker compose logs -f api     # deve mostrar "Application startup complete"
```
A API escuta em `127.0.0.1:8000` (não exposta). Publique `/api/` pelo seu proxy com HTTPS (exemplo em `apps/web/deploy/nginx.conf.example`;
**repasse o cabeçalho Host**).

## 2. Criar a primeira empresa e administrador
```bash
docker compose exec api python -m scripts.provision_admin --company "Minha Empresa" --slug minha-empresa --email voce@empresa.com.br
```
A senha é pedida no terminal (mín. 14 caracteres) e não é gravada em arquivo.
Produção **não** tem usuários de demonstração (`DEMO_SEED=false`).

## 3. Publicar o site
Extraia `talentflow-web-vX.Y.Z.zip` na pasta do seu servidor web e siga `DEPLOY-WEB.md` (dentro do ZIP).

## 4. Aplicativos
Baixe o APK e o instalador `.exe` em **GitHub Releases**. Ao abrir, informe o endereço do seu servidor (o mesmo do site).

## Backup e restauração
```bash
./backup.sh 14        # dump comprimido em infra/backups, mantém 14 dias. Agende no cron e copie para FORA do servidor.
./restore.sh backups/talentflow-AAAAMMDD-HHMMSS.dump   # pede confirmação; substitui os dados
```
Os currículos ficam no volume `uploads`; inclua-o no seu backup de volumes.

## Atualizar
`git pull && docker compose up -d --build` (migrações rodam no início). Faça backup antes.

## Variáveis
| Variável | Para quê |
|---|---|
| `PGDATABASE`, `PGUSER`, `PGPASSWORD` | PostgreSQL (a senha é obrigatória) |
| `TRUSTED_ORIGINS` | origens do site aceitas em escritas (login). Obrigatória em produção |
| `CORS_ORIGINS` | só se o site ficar em outro domínio |
| `COOKIE_SECURE` | `true` em produção (fixado no compose) |
| `TF_LOGIN_IP_LIMIT` | tentativas de login por IP em 15 min (padrão 40) |
| `ENABLE_LEGACY_WORKSPACE` | `true` reativa o snapshot v1.1 (não recomendado) |

## Não validado
O `docker compose` **não foi executado** no ambiente de desenvolvimento (sem daemon Docker). O Dockerfile e a imagem são
exercitados indiretamente pelo CI (API em PostgreSQL 16) mas o fluxo `docker compose up` completo ainda precisa de um teste real.
