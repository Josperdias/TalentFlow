#!/usr/bin/env python3
"""Exporta o contrato OpenAPI v1 para packages/contracts/openapi.json (usado pelos 3 clientes e pelo CI)."""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'services' / 'api'))
os.environ.setdefault('DATABASE_URL', 'sqlite:////tmp/tf-openapi.db')
os.environ.setdefault('APP_ENV', 'test')
from app.main import app  # noqa: E402
spec = app.openapi()
out = ROOT / 'packages' / 'contracts' / 'openapi.json'
out.write_text(json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
print(f'{out.relative_to(ROOT)}: {len(spec["paths"])} caminhos, versão {spec["info"]["version"]}')
