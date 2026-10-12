"""Security and new lifecycle tests. Run alongside test_flow.py (shared test DB)."""
import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app


def auth(c,email='admin@nexa.demo'):
    result=c.post('/api/auth/login',json={'email':email,'password':'Demo@2026!'})
    assert result.status_code==200,result.text
    csrf=c.get('/api/auth/csrf')
    assert csrf.status_code==200
    c.headers['X-TF-CSRF']=csrf.json()['token']


def test_csrf_fetch_metadata_headers_and_sessions():
    with TestClient(app) as c:
        auth(c)
        rows=c.get('/api/auth/sessions');assert rows.status_code==200
        missing=c.post('/api/jobs',json={'title':'Não deve criar'},headers={'X-TF-CSRF':''})
        assert missing.status_code==403
        forged=c.post('/api/jobs',json={'title':'Não deve criar'},headers={'Origin':'https://evil.example'})
        assert forged.status_code==403
        forged_site=c.post('/api/jobs',json={'title':'Não deve criar'},headers={'Sec-Fetch-Site':'cross-site'})
        assert forged_site.status_code==403
        normal=c.post('/api/jobs',json={'title':'Gestão da Segurança'})
        assert normal.status_code==200,normal.text
        h=c.get('/api/health')
        assert 'script-src' in h.headers['Content-Security-Policy']
        assert h.headers['Cache-Control']=='no-store'
    with TestClient(app) as a,TestClient(app) as b:
        auth(a);auth(b)
        r=a.post('/api/auth/sessions/revoke-others')
        assert r.status_code==200 and r.json()['revoked']>=1
        assert b.get('/api/me').status_code==401
        assert a.get('/api/me').status_code==200


def test_rate_limit_unknown_account_is_persistent():
    with TestClient(app) as c:
        for _ in range(8):
            r=c.post('/api/auth/login',json={'email':'bad-traffic@example.invalid','password':'wrong'})
            assert r.status_code==401,r.text
        r=c.post('/api/auth/login',json={'email':'bad-traffic@example.invalid','password':'wrong'})
        assert r.status_code==429 and r.headers.get('retry-after')
    with TestClient(app) as c2:
        assert c2.post('/api/auth/login',json={'email':'bad-traffic@example.invalid','password':'wrong'}).status_code==429


def test_pdi_actions_and_tenant_isolation():
    with TestClient(app) as c:
        auth(c)
        e=next(e for e in c.get('/api/lifecycle/employees').json() if e['status']=='active')
        pid=e['id']
        d=c.post('/api/workforce/plans',json={'employee_id':pid,'title':'Exercícios de comunicação','competency':'Comunicação','goal':'Registrar apresentações e devolutivas mensais','due_date':'2027-02-28','actions':['Fazer estudo guiado','Apresentar na reunião']})
        assert d.status_code==200,d.text
        plan=d.json();assert plan['progress']==0
        r=c.post(f'/api/workforce/plans/{plan["id"]}/action',json={'index':0,'done':True,'evidence':'Apresentação realizada'})
        assert r.json()['progress']==50
        r=c.post(f'/api/workforce/plans/{plan["id"]}/action',json={'index':1,'done':True,'evidence':'Feedback escrito'})
        assert r.json()['status']=='completed'
        r=c.post(f'/api/workforce/plans/{plan["id"]}/action',json={'index':1,'done':False})
        assert r.json()['progress']==50
        assert c.get('/api/workforce/insights').json()['population']>=20
        assert c.post(f'/api/workforce/plans/{plan["id"]}/archive').status_code==200
        assert c.post(f'/api/workforce/plans/{plan["id"]}/action',json={'index':0,'done':False}).status_code==409
    with TestClient(app) as other:
        auth(other,'admin@orbe.demo')
        assert other.get('/api/workforce/plans').json()==[]
        assert other.get('/api/workforce/insights').json()['population']==0
        assert other.post(f'/api/workforce/plans/{plan["id"]}/archive').status_code==404


def test_leave_approval_overlap_and_permissions():
    with TestClient(app) as c:
        auth(c)
        e=next(e for e in c.get('/api/lifecycle/employees').json() if e['status']=='active')
        payload={'employee_id':e['id'],'kind':'vacation','starts_on':'2027-05-10','ends_on':'2027-05-15'}
        r=c.post('/api/workforce/leaves',json=payload)
        assert r.status_code==200,r.text
        lid=r.json()['id'];assert r.json()['days']==6
        assert c.post('/api/workforce/leaves',json=payload).status_code==409
        assert c.post('/api/workforce/leaves',json={**payload,'starts_on':'2027-05-21','ends_on':'2027-05-15'}).status_code==422
        decision=c.post(f'/api/workforce/leaves/{lid}/decide',json={'decision':'approved','comment':'Cobertura ajustada'})
        assert decision.status_code==200
        assert c.post(f'/api/workforce/leaves/{lid}/decide',json={'decision':'rejected'}).status_code==409
        assert any(e['id']==lid for e in c.get('/api/workforce/leaves').json())
    with TestClient(app) as c:
        auth(c,'recrutador@nexa.demo')
        assert c.post(f'/api/workforce/leaves/{lid}/decide',json={'decision':'rejected'}).status_code==403
    with TestClient(app) as c:
        auth(c,'admin@orbe.demo')
        assert c.post(f'/api/workforce/leaves/{lid}/decide',json={'decision':'rejected'}).status_code==404


def test_upload_content_not_extension():
    with TestClient(app) as c:
        auth(c)
        who=c.post('/api/candidates',json={'name':'Currículo Seguro','email':'seguro.teste@example.com'}).json()['id']
        assert c.post(f'/api/candidates/{who}/resume',files={'file':('arquivo.pdf',b'MZfake-executable','application/pdf')}).status_code==422
        assert c.post(f'/api/candidates/{who}/resume',files={'file':('arquivo.docx',b'PKnot-valid-zip','application/vnd.openxmlformats-officedocument.wordprocessingml.document')}).status_code==422
