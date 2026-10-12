"""API v1 para clientes nativos: tokens, rotação de refresh, isolamento, conflito e feed de mudanças."""
import threading
import pytest
from fastapi.testclient import TestClient
from app.main import app

PW='Demo@2026!'

@pytest.fixture(scope='module')
def boot():
    with TestClient(app):  # dispara lifespan (cria schema e seed) uma vez
        yield

def native(email='admin@nexa.demo',client='android',device='Pixel 8'):
    c=TestClient(app)
    r=c.post('/api/v1/auth/token',json={'email':email,'password':PW,'client':client,'device':device})
    assert r.status_code==200,r.text
    body=r.json()
    c.headers['Authorization']='Bearer '+body['access_token']
    return c,body

def test_token_login_and_me(boot):
    c,body=native()
    assert body['token_type']=='Bearer' and body['expires_in']==900
    assert body['user']['role']=='admin' and body['user']['company']
    assert c.get('/api/v1/me').json()['user']['email']=='admin@nexa.demo'
    assert TestClient(app).get('/api/v1/me').status_code==401

def test_wrong_password_and_unknown_client(boot):
    c=TestClient(app)
    assert c.post('/api/v1/auth/token',json={'email':'admin@nexa.demo','password':'x'}).status_code==401
    assert c.post('/api/v1/auth/token',json={'email':'admin@nexa.demo','password':PW,'client':'hacker'}).status_code==422

def test_cookie_and_bearer_tokens_are_not_interchangeable(boot):
    web=TestClient(app)
    r=web.post('/api/v1/auth/login',json={'email':'admin@nexa.demo','password':PW});assert r.status_code==200
    cookie=web.cookies.get('tf_session')
    assert cookie and r.json()['csrf']
    # cookie de navegador usado como Bearer deve falhar
    assert TestClient(app).get('/api/v1/me',headers={'Authorization':'Bearer '+cookie}).status_code==401
    # access token usado como cookie deve falhar
    _,body=native()
    other=TestClient(app,cookies={'tf_session':body['access_token']})
    assert other.get('/api/v1/me').status_code==401

def test_refresh_rotation_and_reuse_detection(boot):
    c,body=native()
    r1=c.post('/api/v1/auth/refresh',json={'refresh_token':body['refresh_token']})
    assert r1.status_code==200
    new=r1.json()
    assert new['refresh_token']!=body['refresh_token'] and new['access_token']!=body['access_token']
    # reapresentar o refresh antigo = suspeita de roubo -> derruba toda a família
    assert c.post('/api/v1/auth/refresh',json={'refresh_token':body['refresh_token']}).status_code==401
    assert c.post('/api/v1/auth/refresh',json={'refresh_token':new['refresh_token']}).status_code==401
    assert TestClient(app).get('/api/v1/me',headers={'Authorization':'Bearer '+new['access_token']}).status_code==401

def test_logout_revokes_device_session(boot):
    c,body=native()
    assert c.post('/api/v1/auth/logout').status_code==200
    assert c.get('/api/v1/me').status_code==401
    assert TestClient(app).post('/api/v1/auth/refresh',json={'refresh_token':body['refresh_token']}).status_code==401

def test_sessions_listing_and_revoke_others(boot):
    a,_=native(client='android');w,_=native(client='windows',device='PC')
    kinds={s['client'] for s in a.get('/api/v1/auth/sessions').json()}
    assert {'android','windows'}<=kinds
    assert w.post('/api/v1/auth/sessions/revoke-others').json()['revoked']>=1
    assert a.get('/api/v1/me').status_code==401
    assert w.get('/api/v1/me').status_code==200

def test_tenant_isolation_over_bearer(boot):
    nexa,_=native('admin@nexa.demo');orbe,_=native('admin@orbe.demo')
    nexa_jobs={j['id'] for j in nexa.get('/api/v1/jobs').json()}
    orbe_jobs={j['id'] for j in orbe.get('/api/v1/jobs').json()}
    assert nexa_jobs and not (nexa_jobs & orbe_jobs)
    victim=next(iter(nexa_jobs))
    assert orbe.get(f'/api/v1/jobs/{victim}').status_code==404
    assert orbe.patch(f'/api/v1/jobs/{victim}',json={'title':'invadida'},headers={'If-Match':'1'}).status_code==404
    cands={c['id'] for c in nexa.get('/api/v1/candidates').json()}
    assert not ({c['id'] for c in orbe.get('/api/v1/candidates').json()} & cands)

def test_rbac_over_bearer(boot):
    cand,_=native('candidato@nexa.demo')
    assert cand.get('/api/v1/jobs').status_code==403
    assert cand.post('/api/v1/jobs',json={'title':'Vaga indevida'}).status_code==403
    assert cand.get('/api/v1/portal').status_code==200
    mgr,_=native('gestor@nexa.demo')
    assert mgr.post('/api/v1/jobs',json={'title':'Gestor não cria'}).status_code==403
    adm,_=native()
    assert len(mgr.get('/api/v1/jobs').json())<=len(adm.get('/api/v1/jobs').json())

def test_if_match_required_and_conflict_detected_between_clients(boot):
    android,_=native(client='android');windows,_=native(client='windows')
    job=android.post('/api/v1/jobs',json={'title':'Vaga de teste de conflito'}).json()
    assert job['version']==1 and job['code']==f"TF-{job['id']:05}"
    # sem If-Match: 428
    assert android.patch(f"/api/v1/jobs/{job['id']}",json={'title':'Sem versão'}).status_code==428
    # Android salva primeiro
    ok=android.patch(f"/api/v1/jobs/{job['id']}",json={'title':'Editada no Android'},headers={'If-Match':'1'})
    assert ok.status_code==200 and ok.json()['version']==2
    # Windows ainda tem a versão 1 -> não pode sobrescrever em silêncio
    stale=windows.patch(f"/api/v1/jobs/{job['id']}",json={'title':'Editada no Windows'},headers={'If-Match':'1'})
    assert stale.status_code==409
    detail=stale.json()['detail']
    assert detail['current_version']==2 and detail['current']['title']=='Editada no Android'
    # após atualizar, o Windows consegue salvar
    assert windows.patch(f"/api/v1/jobs/{job['id']}",json={'title':'Revisada no Windows'},headers={'If-Match':'2'}).json()['version']==3
    assert android.get(f"/api/v1/jobs/{job['id']}").json()['job']['title']=='Revisada no Windows'

def test_application_move_conflict(boot):
    a,_=native(client='android');w,_=native(client='windows')
    app_=detail=None
    for job in a.get('/api/v1/jobs').json():
        detail=a.get(f"/api/v1/jobs/{job['id']}").json()
        app_=next((x for x in detail['applications'] if x['status']=='active'),None)
        if app_:break
    assert app_,'seed deve conter ao menos uma candidatura ativa'
    stages=[s for s in detail['stages'] if s['kind']=='active' and s['id']!=app_['stage_id']]
    v=app_['version']
    assert a.post(f"/api/v1/applications/{app_['id']}/move",json={'stage_id':stages[0]['id']}).status_code==428
    ok=a.post(f"/api/v1/applications/{app_['id']}/move",json={'stage_id':stages[0]['id']},headers={'If-Match':str(v)})
    assert ok.status_code==200 and ok.json()['version']>v
    stale=w.post(f"/api/v1/applications/{app_['id']}/move",json={'stage_id':stages[-1]['id']},headers={'If-Match':str(v)})
    assert stale.status_code==409

def test_pdi_conflict(boot):
    a,_=native();w,_=native(client='windows')
    plans=a.get('/api/v1/workforce/plans').json()
    p=next(x for x in plans if x['status']=='active')
    assert 'version' in p
    body={'index':0,'done':True,'evidence':'Concluído via Android'}
    assert a.post(f"/api/v1/workforce/plans/{p['id']}/action",json=body).status_code==428
    r=a.post(f"/api/v1/workforce/plans/{p['id']}/action",json=body,headers={'If-Match':str(p['version'])})
    assert r.status_code==200
    assert w.post(f"/api/v1/workforce/plans/{p['id']}/action",json={**body,'evidence':'Windows'},headers={'If-Match':str(p['version'])}).status_code==409

def test_change_feed_propagates_between_clients(boot):
    web,_=native(client='android');win,_=native(client='windows')
    start=win.get('/api/v1/changes/cursor').json()['cursor']
    created=web.post('/api/v1/jobs',json={'title':'Criada no cliente A'}).json()
    feed=win.get('/api/v1/changes',params={'after':start}).json()
    assert any(i['entity']=='job' and i['entity_id']==created['id'] for i in feed['items'])
    assert 'job' in feed['entities'] and feed['cursor']>start
    # o outro cliente enxerga o mesmo registro pela API autorizada
    assert any(j['id']==created['id'] for j in win.get('/api/v1/jobs').json())
    # a empresa Orbe não vê mudanças da Nexa
    orbe,_=native('admin@orbe.demo')
    leaked=orbe.get('/api/v1/changes',params={'after':0,'limit':500}).json()['items']
    assert all(i['entity_id']!=created['id'] or i['entity']!='job' for i in leaked)

def test_feed_hides_entity_ids_from_restricted_roles(boot):
    mgr,_=native('gestor@nexa.demo');adm,_=native()
    adm.post('/api/v1/jobs',json={'title':'Gera evento'})
    items=mgr.get('/api/v1/changes',params={'after':0,'limit':50}).json()['items']
    assert items and all(i['entity_id'] is None and i['actor_id'] is None for i in items)

def test_job_codes_unique_under_concurrency(boot):
    c,_=native()
    codes,errors=[],[]
    def create(n):
        try:
            r=TestClient(app,headers=c.headers).post('/api/v1/jobs',json={'title':f'Concorrente {n}'})
            (codes if r.status_code==200 else errors).append(r.json().get('code') if r.status_code==200 else r.status_code)
        except Exception as e:errors.append(repr(e))
    ts=[threading.Thread(target=create,args=(i,)) for i in range(12)]
    [t.start() for t in ts];[t.join() for t in ts]
    assert not errors,errors
    assert len(codes)==12 and len(set(codes))==12

def test_openapi_exposes_v1_only(boot):
    spec=TestClient(app).get('/api/openapi.json').json()
    assert spec['info']['version']=='1.0.0'
    paths=spec['paths']
    assert '/api/v1/jobs' in paths and '/api/v1/auth/token' in paths and '/api/v1/changes' in paths
    assert not [p for p in paths if p.startswith('/api/') and not p.startswith('/api/v1/')]


def test_account_rate_limit_still_enforced(boot):
    c=TestClient(app)
    codes=[c.post('/api/v1/auth/token',json={'email':'forca.bruta@nexa.demo','password':'errada'}).status_code for _ in range(10)]
    assert codes[:8]==[401]*8 and 429 in codes[8:]
