"""Alembic: DATABASE_URL obrigatório; metadata = todos os modelos SQLAlchemy."""
import os
from alembic import context
from sqlalchemy import create_engine, pool

from app.models import Base
import app.workspace  # noqa: F401  registra workspace_snapshots (legado/importação)

config = context.config
url = os.environ.get('DATABASE_URL')
if not url:
    raise SystemExit('Defina DATABASE_URL (ex.: postgresql+psycopg://usuario:senha@host/banco)')
target_metadata = Base.metadata


def run_offline():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_online():
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata, compare_type=True,
                          render_as_batch=url.startswith('sqlite'))
        with context.begin_transaction():
            context.run_migrations()


run_offline() if context.is_offline_mode() else run_online()
