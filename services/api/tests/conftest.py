"""Always isolate test data from shipped demonstration/production databases.
Pytest imports this file before test modules, including those that import app.main.
"""
import os,tempfile
from pathlib import Path

TEST_DB=Path(tempfile.gettempdir())/'talentflow_test_suite_20261011.db'
os.environ['DATABASE_URL']=f'sqlite:///{TEST_DB}'
os.environ['APP_ENV']='test'
os.environ['DEMO_SEED']='true'
