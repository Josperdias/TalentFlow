"""Atualização dos aplicativos nativos hospedada no PRÓPRIO servidor.

O dono do servidor copia para TF_UPDATES_DIR o instalador publicado pelo CI e o manifesto `windows.json`:
    {"version": "1.3.1", "file": "TalentFlow-Setup-v1.3.1.exe", "sha256": "<64 hex>", "notes": "..."}
A API só serve o arquivo citado no manifesto, confere o SHA-256 real do arquivo contra o manifesto e exige login.
Sem TF_UPDATES_DIR (ou sem manifesto) o endpoint responde {"available": false}. Nada é baixado de terceiros.
"""
import hashlib
import json
import os
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from .models import User
from .security import current_user

router = APIRouter(prefix='/api/v1/client-updates', tags=['Atualizações'])

_VERSION = re.compile(r'^\d+\.\d+\.\d+(-[0-9A-Za-z.\-]+)?$')
_FILE = re.compile(r'^TalentFlow-Setup-v[0-9A-Za-z.\-]+\.exe$')
_SHA = re.compile(r'^[0-9a-fA-F]{64}$')
_hash_cache: dict[tuple[str, int, int], str] = {}


def _dir() -> Path | None:
    d = os.getenv('TF_UPDATES_DIR', '').strip()
    return Path(d) if d else None


def _sha256(path: Path) -> str:
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


def _manifest(platform: str) -> tuple[dict, Path] | tuple[None, str]:
    base = _dir()
    if base is None:
        return None, 'Atualizações não configuradas neste servidor.'
    mf = base / f'{platform}.json'
    if not mf.is_file():
        return None, 'Nenhuma atualização publicada.'
    try:
        data = json.loads(mf.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None, 'Manifesto ilegível.'
    ok = (isinstance(data, dict) and _VERSION.match(str(data.get('version', ''))) and _FILE.match(str(data.get('file', '')))
          and _SHA.match(str(data.get('sha256', ''))))
    if not ok:
        return None, 'Manifesto inválido.'
    f = base / data['file']
    if not f.is_file():
        return None, 'Arquivo do instalador ausente.'
    if _sha256(f) != data['sha256'].lower():
        return None, 'O instalador não confere com o SHA-256 do manifesto.'
    return data, f


@router.get('/windows', summary='Atualização disponível para o aplicativo Windows')
def windows_update(_: User = Depends(current_user)):
    data, ref = _manifest('windows')
    if data is None:
        return {'available': False, 'reason': ref}
    return {'available': True, 'version': data['version'], 'url': f"/api/v1/client-updates/windows/download/{data['file']}",
            'sha256': data['sha256'].lower(), 'size': ref.stat().st_size, 'notes': str(data.get('notes', ''))[:2000]}


@router.get('/windows/download/{filename}', summary='Baixa o instalador publicado (somente o do manifesto)')
def windows_download(filename: str, _: User = Depends(current_user)):
    data, ref = _manifest('windows')
    if data is None or filename != data['file']:
        raise HTTPException(404, 'Instalador não encontrado')
    return FileResponse(ref, media_type='application/octet-stream', filename=data['file'])
