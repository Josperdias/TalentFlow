#!/usr/bin/env node
// Servidor de TESTE do pacote web: estático + proxy /api -> API. Sem dependências.
// Uso: node scripts/serve-dist.mjs <pasta-do-site> [porta=8080] [api=http://127.0.0.1:8000]
// Não é para produção: em produção use Nginx/Apache (veja DEPLOY-WEB.md).
import { createServer, request } from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { extname, join, normalize, resolve } from 'node:path';
const [dirArg = 'dist', portArg = '8080', apiArg = 'http://127.0.0.1:8000'] = process.argv.slice(2);
const root = resolve(dirArg), api = new URL(apiArg);
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.woff': 'font/woff', '.png': 'image/png' };
createServer((req, res) => {
  if (req.url.startsWith('/api/')) {
    const up = request({ host: api.hostname, port: api.port, path: req.url, method: req.method, headers: req.headers } /* preserva o Host original, como `proxy_set_header Host $host` no Nginx */, r => { res.writeHead(r.statusCode, r.headers); r.pipe(res); });
    up.on('error', () => { res.writeHead(502, { 'content-type': 'application/json' }); res.end('{"detail":"API indisponível"}'); });
    return req.pipe(up);
  }
  let file = join(root, normalize(decodeURIComponent(req.url.split('?')[0])).replace(/^(\.\.[/\\])+/, ''));
  if (!existsSync(file) || statSync(file).isDirectory()) file = join(root, 'index.html');
  const ext = extname(file);
  const sec = { 'x-content-type-options': 'nosniff', 'referrer-policy': 'no-referrer', 'x-frame-options': 'DENY',
    'content-security-policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'; form-action 'self'" }; // mesma política do exemplo de Nginx
  res.writeHead(200, { ...sec, 'content-type': types[ext] ?? 'application/octet-stream', 'cache-control': file.includes('/assets/') ? 'public, max-age=31536000, immutable' : 'no-store' });
  createReadStream(file).pipe(res);
}).listen(Number(portArg), '127.0.0.1', () => console.log(`site: http://127.0.0.1:${portArg}  (api -> ${apiArg})`));
