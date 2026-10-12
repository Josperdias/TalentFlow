"""Server-side controls for the connected v1.1 HTML workspace."""
import copy
import os
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.main import app
from app.database import SessionLocal
from app.models import AuditLog


def signin(client,email='admin@nexa.demo'):
    r=client.post('/api/auth/login',json={'email':email,'password':'Demo@2026!'})
    assert r.status_code==200,r.text
    token=client.get('/api/auth/csrf')
    assert token.status_code==200
    client.headers['X-TF-CSRF']=token.json()['token']


def test_requires_login_role_and_csrf():
    with TestClient(app) as c:
        assert c.get('/workspace').status_code==401
        assert c.get('/api/workspace/state').status_code==401
        signin(c,'recrutador@nexa.demo')
        assert c.get('/workspace').status_code==403
        assert c.get('/api/workspace/state').status_code==403
        assert c.post('/api/workspace/state',json={'version':1,'data':{'jobs':[],'applications':[]}}).status_code==403
    with TestClient(app) as admin:
        signin(admin)
        r=admin.get('/workspace')
        assert r.status_code==200
        assert 'workspace.js' in r.text
        assert 'Cache-Control' in r.headers and r.headers['Cache-Control']=='no-store'
        assert admin.get('/assets/workspace.js').status_code==200
        assert admin.get('/assets/workspace.html').status_code==404
        metrics=admin.get('/api/workspace/metrics')
        assert metrics.status_code==200 and metrics.json()['counts']['jobs']>=10
        row=admin.get('/api/workspace/state').json()
        assert isinstance(row['state']['jobs'],list) and len(row['state']['jobs'])==10
        denied=admin.post('/api/workspace/state',json={'version':row['version'],'data':row['state']},headers={'X-TF-CSRF':''})
        assert denied.status_code==403


def test_version_guard_audited_and_tenant_isolation():
    with TestClient(app) as nexa,TestClient(app) as orbe:
        signin(nexa)
        signin(orbe,'admin@orbe.demo')
        n=nexa.get('/api/workspace/state').json()
        o=orbe.get('/api/workspace/state').json()
        assert n['version']>=1 and o['version']>=1
        initial_orbe=len(o['state']['jobs'])
        payload=copy.deepcopy(n['state'])
        title='QA version guard v12'
        payload['jobs'].append({**payload['jobs'][0],'id':900001,'title':title})
        updated=nexa.post('/api/workspace/state',json={'version':n['version'],'data':payload})
        assert updated.status_code==200,updated.text
        assert updated.json()['version']==n['version']+1
        assert 'jobs' in updated.json()['changed']
        assert len(nexa.get('/api/workspace/state').json()['state']['jobs'])==len(n['state']['jobs'])+1
        assert len(orbe.get('/api/workspace/state').json()['state']['jobs'])==initial_orbe
        assert nexa.post('/api/workspace/state',json={'version':n['version'],'data':n['state']}).status_code==409
        with SessionLocal() as db:
            rows=db.scalars(select(AuditLog).where(AuditLog.action=='workspace_changed')).all()
            assert any('jobs' in row.after_json['collections'] for row in rows)
        # Restore only our own dataset to avoid contaminating subsequent tests.
        latest=nexa.get('/api/workspace/state').json()
        restored=nexa.post('/api/workspace/state',json={'version':latest['version'],'data':n['state']})
        assert restored.status_code==200


def test_payload_limits_and_no_demo_in_production(monkeypatch):
    from app.workspace import validate_snapshot,seed_state
    from fastapi import HTTPException
    try:validate_snapshot({'jobs':[],'applications':[],'x':'a'*2_000_001})
    except HTTPException as e:assert e.status_code==413
    else:assert False,'oversized payload accepted'
    try:validate_snapshot({'jobs':[],'applications':[],'__proto__':{}})
    except HTTPException as e:assert e.status_code==422
    else:assert False,'unsafe field accepted'
    monkeypatch.setenv('APP_ENV','production')
    assert seed_state()['candidates']==[]
