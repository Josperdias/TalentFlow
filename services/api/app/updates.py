"""Atualização dos aplicativos nativos (Windows e Android) sem abrir o navegador.

O aplicativo pergunta a ESTE servidor se há versão mais nova; o servidor decide a origem:
 1) pasta própria (TF_UPDATES_DIR): `windows.json` / `android.json` + o arquivo citado; ou
 2) Releases do GitHub (TF_UPDATES_GITHUB_REPO=dono/repositorio): a build nova publicada vira atualização sozinha.
    Para repositório privado, TF_UPDATES_GITHUB_TOKEN (somente leitura) fica SÓ no servidor, nunca nos aplicativos.
Em ambos os casos: exige login, o SHA-256 vem do manifesto/arquivo `.sha256` da release e o aplicativo recusa o que não conferir.
Sem nenhuma origem configurada, responde {"available": false}.
"""
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from .models import User
from .security import current_user

router = APIRouter(prefix='/api/v1/client-updates', tags=['Atualizações'])

PLATFORMS = {
    # padrão do arquivo instalável, extensão e arquivo de manifesto
    'windows': {'file': re.compile(r'^TalentFlow-Setup-v[0-9A-Za-z.\-]+\.exe$'), 'ext': '.exe'},
    'android': {'file': re.compile(r'^talentflow-android-v[0-9A-Za-z.\-]+\.apk$'), 'ext': '.apk'},
}
_VERSION = re.compile(r'^\d+\.\d+\.\d+(-[0-9A-Za-z.\-]+)?$')
_SHA = re.compile(r'^[0-9a-fA-F]{64}$')
_hash_cache: dict[tuple[str, int, int], str] = {}
_gh_cache: dict[str, tuple[float, object]] = {}


def version_key(v: str):
    """Precedência semântica: 1.3.0-rc.1 < 1.3.0-rc.2 < 1.3.0."""
    v = v.split('+')[0].lstrip('v')
    core, _, pre = v.partition('-')
    nums = tuple(int(p) if p.isdigit() else 0 for p in core.split('.'))
    if not pre:
        return (nums, 1, ())
    return (nums, 0, tuple((0, int(p), '') if p.isdigit() else (1, 0, p) for p in pre.split('.')))


# ------------------------------------------------------------------ origem 1: pasta própria
def _dir() -> Path | None:
    d = os.getenv('TF_UPDATES_DIR', '').strip()
    return Path(d) if d else None


def _sha256_file(path: Path) -> str:
    st = path.stat()
    key = (str(path), st.st_mtime_ns, st.st_size)
    if key not in _hash_cache:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
        _hash_cache.clear()
        _hash_cache[key] = h.hexdigest()
    return _hash_cache[key]


def _from_dir(platform: str) -> dict | None:
    base = _dir()
    if base is None:
        return None
    mf = base / f'{platform}.json'
    if not mf.is_file():
        return None
    try:
        data = json.loads(mf.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not (isinstance(data, dict) and _VERSION.match(str(data.get('version', ''))) and PLATFORMS[platform]['file'].match(str(data.get('file', '')))
            and _SHA.match(str(data.get('sha256', '')))):
        return None
    f = base / data['file']
    if not f.is_file() or _sha256_file(f) != data['sha256'].lower():
        return None
    return {'version': data['version'], 'file': data['file'], 'sha256': data['sha256'].lower(), 'size': f.stat().st_size,
            'notes': str(data.get('notes', ''))[:2000], 'channel': str(data.get('channel', 'release')), 'source': 'dir', 'path': f}


# ------------------------------------------------------------------ origem 2: Releases do GitHub
def _gh_headers(accept='application/vnd.github+json') -> dict:
    h = {'Accept': accept, 'User-Agent': 'TalentFlow-People-Updater', 'X-GitHub-Api-Version': '2022-11-28'}
    tok = os.getenv('TF_UPDATES_GITHUB_TOKEN', '').strip()
    if tok:
        h['Authorization'] = f'Bearer {tok}'
    return h


def _gh_get_json(url: str):
    ttl = int(os.getenv('TF_UPDATES_CACHE_SECONDS', '600') or 600)
    hit = _gh_cache.get(url)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    req = urllib.request.Request(url, headers=_gh_headers())
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode('utf-8'))
    _gh_cache[url] = (time.time(), data)
    return data


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # noqa: D401
        return None


def _gh_open_asset(asset: dict):
    """Abre o conteúdo do asset. Com token (repositório privado) pede o redirecionamento assinado SEM repassar o token ao destino."""
    if os.getenv('TF_UPDATES_GITHUB_TOKEN', '').strip():
        req = urllib.request.Request(asset['url'], headers=_gh_headers('application/octet-stream'))
        try:
            return urllib.request.build_opener(_NoRedirect).open(req, timeout=20)
        except urllib.error.HTTPError as e:
            loc = e.headers.get('Location') if e.code in (301, 302, 303, 307) else None
            if not loc:
                raise
            return urllib.request.urlopen(urllib.request.Request(loc, headers={'User-Agent': 'TalentFlow-People-Updater'}), timeout=30)
    return urllib.request.urlopen(urllib.request.Request(asset['browser_download_url'], headers={'User-Agent': 'TalentFlow-People-Updater'}), timeout=30)


def _gh_read_sha(asset: dict) -> str | None:
    with _gh_open_asset(asset) as r:
        text = r.read(4096).decode('utf-8', 'ignore')
    m = re.search(r'\b([0-9a-fA-F]{64})\b', text)
    return m.group(1).lower() if m else None


def _from_github(platform: str) -> dict | None:
    repo = os.getenv('TF_UPDATES_GITHUB_REPO', '').strip()
    if not repo or not re.fullmatch(r'[\w.\-]+/[\w.\-]+', repo):
        return None
    try:
        releases = _gh_get_json(f'https://api.github.com/repos/{repo}/releases?per_page=20')
    except (urllib.error.URLError, OSError, ValueError):
        return None
    allow_pre = os.getenv('TF_UPDATES_PRERELEASES', 'true').strip().lower() not in ('0', 'false', 'no')
    cands = []
    for rel in releases if isinstance(releases, list) else []:
        tag = str(rel.get('tag_name', '')).lstrip('v')
        if rel.get('draft') or (rel.get('prerelease') and not allow_pre) or not _VERSION.match(tag):
            continue
        cands.append((version_key(tag), tag, rel))
    for _, tag, rel in sorted(cands, key=lambda c: c[0], reverse=True):
        assets = {a.get('name', ''): a for a in rel.get('assets', [])}
        names = [n for n in assets if PLATFORMS[platform]['file'].match(n)]
        # prefere o instalável de release (assinado) ao de depuração
        names.sort(key=lambda n: (n.endswith('-debug.apk'), n))
        for n in names:
            sha_asset = assets.get(n + '.sha256')
            if not sha_asset:
                continue
            try:
                sha = _gh_read_sha(sha_asset)
            except (urllib.error.URLError, OSError):
                continue
            if sha:
                return {'version': tag, 'file': n, 'sha256': sha, 'size': int(assets[n].get('size', 0)), 'notes': str(rel.get('body') or '')[:2000],
                        'channel': 'debug' if n.endswith('-debug.apk') else 'release', 'source': 'github', 'asset': assets[n]}
    return None


# ------------------------------------------------------------------ endpoints
def _resolve(platform: str) -> dict | None:
    return _from_dir(platform) or _from_github(platform)


def _platform(platform: str) -> str:
    if platform not in PLATFORMS:
        raise HTTPException(404, 'Plataforma desconhecida')
    return platform


@router.get('/{platform}', summary='Atualização disponível para o aplicativo (windows ou android)')
def update_info(platform: str, _: User = Depends(current_user)):
    m = _resolve(_platform(platform))
    if m is None:
        return {'available': False, 'reason': 'Nenhuma atualização publicada ou origem não configurada.'}
    return {'available': True, 'version': m['version'], 'url': f"/api/v1/client-updates/{platform}/download/{m['file']}", 'sha256': m['sha256'],
            'size': m['size'], 'notes': m['notes'], 'channel': m['channel'], 'source': m['source']}


@router.get('/{platform}/download/{filename}', summary='Baixa o instalável publicado (somente o do manifesto/release)')
def update_download(platform: str, filename: str, _: User = Depends(current_user)):
    m = _resolve(_platform(platform))
    if m is None or filename != m['file']:
        raise HTTPException(404, 'Arquivo não encontrado')
    if m['source'] == 'dir':
        return FileResponse(m['path'], media_type='application/octet-stream', filename=m['file'])
    try:
        upstream = _gh_open_asset(m['asset'])
    except (urllib.error.URLError, OSError):
        raise HTTPException(502, 'Não foi possível obter o arquivo no GitHub')

    def stream():
        with upstream as r:
            while chunk := r.read(1 << 20):
                yield chunk
    headers = {'Content-Disposition': f'attachment; filename="{m["file"]}"'}
    if m['size']:
        headers['Content-Length'] = str(m['size'])
    return StreamingResponse(stream(), media_type='application/octet-stream', headers=headers)
