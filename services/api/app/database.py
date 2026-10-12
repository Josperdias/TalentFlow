import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
ROOT=Path(__file__).resolve().parent.parent
DATABASE_URL=os.environ.get('DATABASE_URL',f'sqlite:///{ROOT/"talentflow.db"}')
engine=create_engine(DATABASE_URL, connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine,expire_on_commit=False)
def get_db():
    with SessionLocal() as db: yield db
def init_db(): Base.metadata.create_all(bind=engine)
