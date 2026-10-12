"""Isola os testes dos bancos de demonstração/produção.

Por padrão usa SQLite temporário. Defina TF_TEST_DATABASE_URL (PostgreSQL) para
executar a mesma suíte contra um servidor real; o banco é recriado do zero.
Importado pelo pytest antes dos módulos de teste (que importam app.main).
"""
import os,tempfile
from pathlib import Path

_pg=os.environ.get('TF_TEST_DATABASE_URL')
if _pg:
    os.environ['DATABASE_URL']=_pg
else:
    _db=Path(tempfile.gettempdir())/'talentflow_test_suite_20261011.db'
    _db.unlink(missing_ok=True)
    os.environ['DATABASE_URL']=f"sqlite:///{_db}"
os.environ['APP_ENV']='test'
os.environ['TF_LOGIN_IP_LIMIT']='100000'  # a suíte faz centenas de logins do mesmo IP; o limite por conta segue ativo
os.environ['DEMO_SEED']='true'

if _pg:
    from sqlalchemy import create_engine
    from app.models import Base
    import app.workspace  # noqa: F401  (registra workspace_snapshots no metadata)
    _e=create_engine(_pg)
    Base.metadata.drop_all(_e); Base.metadata.create_all(_e); _e.dispose()
