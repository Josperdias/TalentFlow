"""TalentFlow ATS API. All private reads/writes are company scoped."""
from contextlib import asynccontextmanager
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import hashlib,re,secrets,os,io,subprocess,tempfile
from typing import Literal
from fastapi import FastAPI,Depends,HTTPException,Request,Response,UploadFile,File,Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,EmailStr,field_validator
from sqlalchemy import select,func,update
from sqlalchemy.orm import Session
from .database import get_db,init_db,DATABASE_URL
from .seed import seed_if_empty
from .lifecycle_seed import seed_lifecycle_if_empty
from .lifecycle import router as lifecycle_router
from .workforce import router as workforce_router
from .workforce_seed import seed_workforce_if_empty
from .workspace import router as workspace_router
from .auth_v1 import router as auth_v1_router
from .sync import router as sync_router
from .updates import router as updates_router
from sqlalchemy.orm.exc import StaleDataError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .models import *
from .security import allowed,current_user,verify_password,create_session
from .adapters import ai_service,communications,LocalPrivateStorage
from .hardening import csrf_value, validate_browser_request, rate_limit, reset_rate_limit, check_version

ROOT=Path(__file__).resolve().parent.parent
@asynccontextmanager
async def lifespan(app):
    if os.getenv('APP_ENV','development').lower() == 'production':
        if not DATABASE_URL.startswith(('postgresql://','postgresql+psycopg://')):
            raise RuntimeError('Produção exige banco PostgreSQL independente da base de demonstração')
        if os.getenv('COOKIE_SECURE','').lower() != 'true':
            raise RuntimeError('Produção exige COOKIE_SECURE=true e HTTPS')
        if os.getenv('DEMO_SEED','false').lower()=='true':
            raise RuntimeError('Dados e credenciais de demonstração são proibidos em produção')
    if os.getenv('APP_ENV','development').lower()=='production':
        # Produção: o schema só evolui por migrações Alembic (alembic upgrade head), nunca por create_all.
        from sqlalchemy import inspect
        from .database import engine
        if not inspect(engine).has_table('alembic_version'):
            raise RuntimeError('Banco sem migrações aplicadas. Execute: alembic upgrade head')
    else:
        init_db()
    if os.getenv('APP_ENV','development').lower() != 'production' and os.getenv('DEMO_SEED','true').lower()=='true':
        seed_if_empty();seed_lifecycle_if_empty();seed_workforce_if_empty()
    yield
app=FastAPI(title='TalentFlow People API',version='1.0.0',lifespan=lifespan,docs_url='/api/docs',openapi_url='/api/openapi.json')
# Legado (/api/*, fora do OpenAPI) para a interface v1.1 + versão estável (/api/v1/*) para os novos clientes.
for _router in (lifecycle_router,workforce_router):
    app.include_router(_router,prefix='/api',include_in_schema=False)
    app.include_router(_router,prefix='/api/v1')
# Snapshot JSONB da v1.1 (somente admin): legado. Desligado em produção, salvo ENABLE_LEGACY_WORKSPACE=true.
if os.getenv('APP_ENV','development').lower()!='production' or os.getenv('ENABLE_LEGACY_WORKSPACE','false').lower()=='true':
    app.include_router(workspace_router,include_in_schema=False)
app.include_router(auth_v1_router)
app.include_router(sync_router)
app.include_router(updates_router)

# CORS só para origens explicitamente listadas (ex.: site em outro domínio). Padrão: nenhuma.
_origins=[o.strip() for o in os.getenv('CORS_ORIGINS','').split(',') if o.strip()]
if _origins:
    app.add_middleware(CORSMiddleware,allow_origins=_origins,allow_credentials=False,
        allow_methods=['GET','POST','PATCH','PUT','DELETE'],allow_headers=['Authorization','Content-Type','If-Match','X-TF-CSRF'],
        expose_headers=['ETag'],max_age=600)

@app.exception_handler(StaleDataError)
async def stale_data(_req,_exc):
    return JSONResponse({'detail':{'message':'O registro foi alterado por outra sessão. Atualize e tente novamente.'}},status_code=409)

# Deny cross-origin mutations and require a per-session CSRF header.
@app.middleware('http')
async def secure_headers(req:Request,call_next):
    try: validate_browser_request(req)
    except HTTPException as err:
        from fastapi.responses import JSONResponse
        return JSONResponse({'detail':err.detail},status_code=err.status_code)
    res=await call_next(req)
    res.headers['X-Content-Type-Options']='nosniff'
    res.headers['Referrer-Policy']='no-referrer'
    res.headers['X-Frame-Options']='DENY'
    res.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    res.headers['Cross-Origin-Resource-Policy']='same-origin'
    # Inline *styles* remain for the legacy SPA, but scripts must come from this origin.
    res.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'; form-action 'self'"
    if req.url.scheme=='https':res.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    if req.url.path.startswith('/api/') or req.url.path=='/workspace':
        res.headers['Cache-Control']='no-store'
    return res

ROLE_EDIT=('admin','recruiter')
ROLE_EVAL=('admin','recruiter','manager','interviewer')
ROLE_VIEW=('admin','recruiter','manager','interviewer')
def obj(db,model,user,id):
    value=db.scalar(select(model).where(model.id==id,model.company_id==user.company_id))
    if not value:raise HTTPException(404,'Registro não encontrado')
    return value

def audit(db,user,action,entity,entity_id,before=None,after=None):
    db.add(AuditLog(company_id=user.company_id,user_id=user.id,action=action,entity=entity,entity_id=entity_id,before_json=before or {},after_json=after or {}))

def activity(db,user,app_id,kind,description,metadata=None):
    db.add(Activity(company_id=user.company_id,application_id=app_id,author_id=user.id,kind=kind,description=description,metadata_json=metadata or {}))

def user_json(u):return dict(id=u.id,name=u.name,email=u.email,role=u.role,company_id=u.company_id)
def job_json(j,applications=0):return dict(id=j.id,code=j.code,title=j.title,department=j.department,location=j.location,modality=j.modality,seniority=j.seniority,employment=j.employment,salary_min=j.salary_min,salary_max=j.salary_max,description=j.description,requirements=j.requirements,benefits=j.benefits,positions=j.positions,status=j.status,due_date=j.due_date,manager_id=j.manager_id,recruiter_id=j.recruiter_id,applications=applications,version=j.version,created_at=j.created_at.isoformat())
def candidate_json(c):return dict(id=c.id,name=c.name,email=c.email,phone=c.phone,location=c.location,title=c.title,source=c.source,skills=c.skills,experience_years=c.experience_years,education=c.education,resume_text=c.resume_text,consent=c.consent,created_at=c.created_at.isoformat())
def app_json(a,c,j,stage):return dict(id=a.id,candidate_id=c.id,job_id=j.id,stage_id=stage.id,stage=stage.name,status=a.status,fit=a.fit,fit_reason=a.fit_reason,version=a.version,last_activity_at=a.last_activity_at.isoformat(),applied_at=a.created_at.isoformat(),candidate=candidate_json(c),job=job_json(j))

def can_access_job(db,user,job):
    if user.role in ('admin','recruiter'):return True
    if user.role=='manager':return job.manager_id==user.id
    if user.role=='interviewer':
        assigned=db.scalar(select(Interview.id).join(Application,Interview.application_id==Application.id).where(
            Interview.company_id==user.company_id,Interview.interviewer_id==user.id,Application.job_id==job.id).limit(1))
        return assigned is not None
    return False

def can_access_application(db,user,a):
    if user.role in ('admin','recruiter'):return True
    job=obj(db,Job,user,a.job_id)
    if user.role=='manager':return job.manager_id==user.id
    if user.role=='interviewer':
        return db.scalar(select(Interview.id).where(Interview.company_id==user.company_id,Interview.application_id==a.id,Interview.interviewer_id==user.id).limit(1)) is not None
    return False

def accessible_app_ids(db,user):
    if user.role in ('admin','recruiter'):
        return [x for x in db.scalars(select(Application.id).where(Application.company_id==user.company_id)).all()]
    if user.role=='manager':
        return [x for x in db.scalars(select(Application.id).join(Job,Application.job_id==Job.id).where(Application.company_id==user.company_id,Job.manager_id==user.id)).all()]
    if user.role=='interviewer':
        return [x for x in db.scalars(select(Interview.application_id).where(Interview.company_id==user.company_id,Interview.interviewer_id==user.id)).all()]
    return []

def get_application(db,user,id):
    a=obj(db,Application,user,id)
    if not can_access_application(db,user,a):raise HTTPException(403,'Candidatura não atribuída')
    c=obj(db,Candidate,user,a.candidate_id);j=obj(db,Job,user,a.job_id);s=obj(db,JobStage,user,a.stage_id)
    return a,c,j,s

class LoginIn(BaseModel):email:str=Field(min_length=3,max_length=254);password:str=Field(min_length=1,max_length=1024)
@app.get('/api/auth/csrf')
def csrf(req:Request,user:User=Depends(current_user)):
    return {'token':csrf_value(req.cookies['tf_session'])}

@app.post('/api/auth/login')
def login(data:LoginIn,response:Response,request:Request,db:Session=Depends(get_db)):
    rate_limit(db,'login-ip',request.client.host if request.client else 'unknown',int(os.getenv('TF_LOGIN_IP_LIMIT','40')))
    rate_limit(db,'login-account',data.email.lower().strip(),8)
    u=db.scalar(select(User).where(User.email==data.email.lower().strip(),User.active.is_(True)))
    if not u or not verify_password(data.password,u.password_hash):raise HTTPException(401,'Credenciais inválidas')
    token=create_session(db,u)
    reset_rate_limit(db,'login-account',data.email.lower().strip())
    response.set_cookie('tf_session',token,httponly=True,secure=os.getenv('COOKIE_SECURE','false').lower()=='true',samesite='lax',path='/',max_age=43200)
    audit(db,u,'login','user',u.id);db.commit()
    return {'user':user_json(u)}
@app.post('/api/auth/logout')
def logout(req:Request,res:Response,user:User=Depends(current_user),db:Session=Depends(get_db)):
    token=req.cookies.get('tf_session','');sess=db.get(Session,hashlib.sha256(token.encode()).hexdigest())
    if sess:db.delete(sess)
    audit(db,user,'logout','user',user.id);db.commit();res.delete_cookie('tf_session');return {'ok':True}
@app.get('/api/auth/sessions')
def session_overview(request:Request,user:User=Depends(current_user),db:Session=Depends(get_db)):
    sessions=db.scalars(select(Session).where(Session.user_id==user.id)).all()
    current=hashlib.sha256(request.cookies['tf_session'].encode()).hexdigest()
    return [{'id':s.id[:12], 'expires_at':s.expires_at.isoformat(), 'current':s.id==current} for s in sessions]

@app.post('/api/auth/sessions/revoke-others')
def revoke_other_sessions(request:Request,user:User=Depends(current_user),db:Session=Depends(get_db)):
    current=hashlib.sha256(request.cookies['tf_session'].encode()).hexdigest()
    others=db.scalars(select(Session).where(Session.user_id==user.id,Session.id!=current)).all()
    for item in others:db.delete(item)
    audit(db,user,'other_sessions_revoked','user',user.id,after={'count':len(others)})
    db.commit();return {'revoked':len(others)}

@app.get('/api/me')
def me(user:User=Depends(current_user),db:Session=Depends(get_db)):
    company=db.get(Company,user.company_id)
    return {'user':user_json(user),'company':company.name}


@app.get('/api/portal')
def candidate_portal(user:User=Depends(allowed('candidate')),db:Session=Depends(get_db)):
    """Candidate can only see applications for their own email in their own company."""
    own=db.scalars(select(Candidate).where(Candidate.company_id==user.company_id,Candidate.email==user.email,Candidate.deleted.is_(False),Candidate.consent.is_(True))).all()
    if not own:return {'applications':[]}
    ids=[c.id for c in own]
    apps=db.scalars(select(Application).where(Application.company_id==user.company_id,Application.candidate_id.in_(ids)).order_by(Application.created_at.desc())).all()
    jobs={j.id:j for j in db.scalars(select(Job).where(Job.company_id==user.company_id,Job.id.in_([a.job_id for a in apps]))).all()}
    stages={s.id:s for s in db.scalars(select(JobStage).where(JobStage.company_id==user.company_id,JobStage.id.in_([a.stage_id for a in apps]))).all()}
    interviews=db.scalars(select(Interview).where(Interview.company_id==user.company_id,Interview.application_id.in_([a.id for a in apps]))).all()
    offers=db.scalars(select(Offer).where(Offer.company_id==user.company_id,Offer.application_id.in_([a.id for a in apps]))).all()
    return {'applications':[{'id':a.id,'job':jobs[a.job_id].title,'company':db.get(Company,a.company_id).name,'stage':stages[a.stage_id].name,'status':a.status,'applied_at':a.created_at.isoformat(),'interviews':[{'starts_at':i.starts_at,'status':i.status,'duration_minutes':i.duration_minutes,'id':i.id} for i in interviews if i.application_id==a.id],'offers':[{'status':o.status,'accept_path':'/oferta/'+o.token if o.status in ('sent','viewed') else None} for o in offers if o.application_id==a.id]} for a in apps if a.job_id in jobs and a.stage_id in stages]}

@app.get('/api/jobs')
def jobs(q:str='',status:str='',user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    stmt=select(Job).where(Job.company_id==user.company_id)
    if status:stmt=stmt.where(Job.status==status)
    if q:stmt=stmt.where(Job.title.ilike(f'%{q}%'))
    if user.role=='manager':stmt=stmt.where(Job.manager_id==user.id)
    if user.role=='interviewer':stmt=stmt.where(Job.id.in_(select(Application.job_id).join(Interview,Interview.application_id==Application.id).where(Interview.company_id==user.company_id,Interview.interviewer_id==user.id)))
    rows=db.scalars(stmt.order_by(Job.created_at.desc())).all()
    counts=dict(db.execute(select(Application.job_id,func.count()).where(Application.company_id==user.company_id).group_by(Application.job_id)).all())
    return [job_json(j,counts.get(j.id,0)) for j in rows]

class JobIn(BaseModel):
    title:str=Field(min_length=3,max_length=200)
    department:str='Tecnologia'
    location:str='Brasília, DF'
    modality:str='Híbrido'
    seniority:str='Pleno'
    employment:str='CLT'
    salary_min:int=Field(default=0,ge=0)
    salary_max:int=Field(default=0,ge=0)
    description:str=''
    requirements:str=''
    benefits:str=''
    positions:int=Field(default=1,ge=1,le=500)
    due_date:str=''
    status:Literal['open','approval','closed','archived']='open'
    @field_validator('title')
    @classmethod
    def trim_title(cls,v):return v.strip()
@app.post('/api/jobs')
def create_job(data:JobIn,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    # O código deriva do id gerado pelo banco (sem max()+1, que colidia sob concorrência).
    j=Job(company_id=user.company_id,code='TF-'+secrets.token_hex(6),**data.model_dump(),recruiter_id=user.id)
    db.add(j);db.flush();db.execute(update(Job).where(Job.id==j.id).values(code=f'TF-{j.id:05}'));db.refresh(j)  # UPDATE direto: não consome a versão otimista
    for i,name in enumerate(['Novos','Triagem','Entrevista RH','Entrevista Gestor','Teste','Finalistas','Proposta','Contratado','Reprovado']):
        db.add(JobStage(company_id=user.company_id,job_id=j.id,name=name,order=i,kind='hired' if i==7 else 'rejected' if i==8 else 'active'))
    audit(db,user,'created','job',j.id,after=data.model_dump());db.commit();return job_json(j)
@app.get('/api/jobs/{job_id}')
def job_detail(job_id:int,user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    j=obj(db,Job,user,job_id)
    if not can_access_job(db,user,j):raise HTTPException(403,'Vaga não atribuída')
    stages=db.scalars(select(JobStage).where(JobStage.company_id==user.company_id,JobStage.job_id==job_id).order_by(JobStage.order)).all()
    apps=db.scalars(select(Application).where(Application.company_id==user.company_id,Application.job_id==job_id).order_by(Application.created_at.desc())).all()
    candidates={c.id:c for c in db.scalars(select(Candidate).where(Candidate.company_id==user.company_id,Candidate.id.in_([a.candidate_id for a in apps]))).all()} if apps else {}
    stage_ids={s.id:s for s in stages}
    return {'job':job_json(j,len(apps)),'stages':[{'id':s.id,'name':s.name,'kind':s.kind,'order':s.order} for s in stages],'applications':[app_json(a,candidates[a.candidate_id],j,stage_ids[a.stage_id]) for a in apps if a.candidate_id in candidates and a.stage_id in stage_ids]}
@app.patch('/api/jobs/{job_id}')
def update_job(job_id:int,data:dict,request:Request,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    j=obj(db,Job,user,job_id)
    check_version(request,j.version,job_json(j))
    allowed_fields=set(JobIn.model_fields)
    for key,value in data.items():
        if key not in allowed_fields:raise HTTPException(422,f'Campo não permitido: {key}')
    before=job_json(j)
    validated=JobIn(**({k:getattr(j,k) for k in allowed_fields}|data))
    for field,value in validated.model_dump().items():setattr(j,field,value)
    audit(db,user,'updated','job',j.id,before=before,after=data);db.commit();return job_json(j)
@app.post('/api/jobs/{job_id}/duplicate')
def duplicate_job(job_id:int,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    j=obj(db,Job,user,job_id);fields={k:getattr(j,k) for k in JobIn.model_fields};fields['title']=j.title+' (cópia)';fields['status']='approval'
    return create_job(JobIn(**fields),user,db)
@app.post('/api/jobs/{job_id}/stages')
def add_stage(job_id:int,data:dict,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    obj(db,Job,user,job_id);name=str(data.get('name','')).strip()[:80]
    if not name:raise HTTPException(422,'Nome obrigatório')
    maximum=db.scalar(select(func.max(JobStage.order)).where(JobStage.company_id==user.company_id,JobStage.job_id==job_id)) or 0
    s=JobStage(company_id=user.company_id,job_id=job_id,name=name,order=maximum+1)
    db.add(s);db.flush();audit(db,user,'created','job_stage',s.id,after={'name':name});db.commit();return {'id':s.id,'name':s.name}

@app.get('/api/candidates')
def candidates(q:str='',source:str='',user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    stmt=select(Candidate).where(Candidate.company_id==user.company_id,Candidate.deleted.is_(False))
    if q:stmt=stmt.where((Candidate.name.ilike(f'%{q}%'))|(Candidate.skills.ilike(f'%{q}%'))|(Candidate.title.ilike(f'%{q}%')))
    if source:stmt=stmt.where(Candidate.source==source)
    if user.role not in ('admin','recruiter'):
        ids=accessible_app_ids(db,user)
        stmt=stmt.where(Candidate.id.in_(select(Application.candidate_id).where(Application.id.in_(ids))))
    rows=db.scalars(stmt.order_by(Candidate.created_at.desc()).limit(300)).all()
    return [candidate_json(c) for c in rows]
class CandidateIn(BaseModel):
    name:str=Field(min_length=3,max_length=200)
    email:EmailStr
    phone:str=''
    location:str=''
    title:str=''
    source:str='Cadastro manual'
    skills:str=''
    experience_years:int=Field(default=0,ge=0,le=80)
    education:str=''
    resume_text:str=''
    consent:bool=True
@app.post('/api/candidates')
def create_candidate(data:CandidateIn,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    c=Candidate(company_id=user.company_id,**data.model_dump());db.add(c);db.flush();audit(db,user,'created','candidate',c.id,after={'name':c.name});db.commit();return candidate_json(c)
@app.get('/api/candidates/{candidate_id}')
def candidate_detail(candidate_id:int,user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    c=obj(db,Candidate,user,candidate_id)
    if user.role not in ('admin','recruiter') and candidate_id not in [a.candidate_id for a in db.scalars(select(Application).where(Application.id.in_(accessible_app_ids(db,user)))).all()]:raise HTTPException(403,'Talento não designado')
    apps=db.scalars(select(Application).where(Application.company_id==user.company_id,Application.candidate_id==candidate_id)).all()
    jobs={j.id:j for j in db.scalars(select(Job).where(Job.company_id==user.company_id)).all()}
    stages={s.id:s for s in db.scalars(select(JobStage).where(JobStage.company_id==user.company_id)).all()}
    return {'candidate':candidate_json(c),'applications':[app_json(a,c,jobs[a.job_id],stages[a.stage_id]) for a in apps if a.job_id in jobs and a.stage_id in stages and can_access_application(db,user,a)]}
@app.post('/api/applications')
def create_application(data:dict,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    job=obj(db,Job,user,int(data.get('job_id',0)));candidate=obj(db,Candidate,user,int(data.get('candidate_id',0)))
    existing=db.scalar(select(Application).where(Application.company_id==user.company_id,Application.job_id==job.id,Application.candidate_id==candidate.id))
    if existing:raise HTTPException(409,'Pessoa já vinculada a esta vaga')
    s=db.scalar(select(JobStage).where(JobStage.job_id==job.id,JobStage.company_id==user.company_id).order_by(JobStage.order))
    a=Application(company_id=user.company_id,candidate_id=candidate.id,job_id=job.id,stage_id=s.id,fit=50);db.add(a);db.flush()
    activity(db,user,a.id,'created','Candidatura criada manualmente');audit(db,user,'created','application',a.id);db.commit()
    return {'id':a.id}

@app.get('/api/applications/{application_id}')
def application_detail(application_id:int,user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    a,c,j,s=get_application(db,user,application_id)
    interviews=db.scalars(select(Interview).where(Interview.company_id==user.company_id,Interview.application_id==a.id).order_by(Interview.created_at.desc())).all()
    scores=db.scalars(select(Scorecard).where(Scorecard.company_id==user.company_id,Scorecard.application_id==a.id)).all()
    logs=db.scalars(select(Activity).where(Activity.company_id==user.company_id,Activity.application_id==a.id).order_by(Activity.created_at.desc())).all()
    messages=db.scalars(select(Communication).where(Communication.company_id==user.company_id,Communication.application_id==a.id).order_by(Communication.created_at.desc())).all()
    offers=db.scalars(select(Offer).where(Offer.company_id==user.company_id,Offer.application_id==a.id).order_by(Offer.created_at.desc())).all()
    resumes=db.scalars(select(Resume).where(Resume.company_id==user.company_id,Resume.candidate_id==c.id).order_by(Resume.created_at.desc())).all()
    return {'resumes':[{'id':r.id,'filename':r.filename,'created_at':r.created_at.isoformat(),'text_chars':len(r.extracted_text)} for r in resumes], 'application':app_json(a,c,j,s),'stages':[{'id':t.id,'name':t.name,'kind':t.kind} for t in db.scalars(select(JobStage).where(JobStage.company_id==user.company_id,JobStage.job_id==j.id).order_by(JobStage.order)).all()], 'interviews':[{'id':v.id,'starts_at':v.starts_at,'duration_minutes':v.duration_minutes,'status':v.status,'notes':v.notes,'meeting_link':v.meeting_link} for v in interviews], 'scorecards':[{'id':v.id,'criteria':v.criteria,'result':v.result,'notes':v.notes,'created_at':v.created_at.isoformat()} for v in scores], 'activities':[{'id':v.id,'kind':v.kind,'description':v.description,'created_at':v.created_at.isoformat()} for v in logs], 'communications':[{'id':v.id,'subject':v.subject,'body':v.body,'channel':v.channel,'status':v.status} for v in messages], 'offers':[{'id':v.id,'salary':v.salary,'status':v.status,'start_date':v.start_date,'token':v.token} for v in offers]}

def process_automation(db,user,a,stage):
    rules=db.scalars(select(Automation).where(Automation.company_id==user.company_id,Automation.enabled.is_(True),Automation.trigger=='stage_changed')).all()
    for rule in rules:
        if rule.condition_json.get('stage') and rule.condition_json['stage']!=stage.name:continue
        try:
            action=rule.action_json
            if action.get('type')=='email':
                communications.queue(db,user.company_id,a.id,'email',action.get('template','Atualização'),'Comunicação automática preparada em modo demonstração. Nenhum e-mail externo foi enviado.')
            elif action.get('type')=='task':
                db.add(Task(company_id=user.company_id,application_id=a.id,title=action.get('title','Acompanhar candidato'),assignee_id=user.id))
            rule.runs+=1
            db.add(AutomationRun(company_id=user.company_id,automation_id=rule.id,application_id=a.id,status='success',detail='Ação executada no provedor mock'))
        except Exception as exc:
            db.add(AutomationRun(company_id=user.company_id,automation_id=rule.id,application_id=a.id,status='error',detail=str(exc)[:200]))

@app.post('/api/applications/{application_id}/move')
def move(application_id:int,data:dict,request:Request,user:User=Depends(allowed('admin','recruiter','manager')),db:Session=Depends(get_db)):
    a,c,j,old=get_application(db,user,application_id)
    check_version(request,a.version,{'stage_id':old.id,'stage':old.name,'status':a.status})
    if user.role=='manager' and j.manager_id!=user.id:raise HTTPException(403,'Vaga não atribuída')
    stage=obj(db,JobStage,user,int(data.get('stage_id',0)))
    if stage.job_id!=a.job_id:raise HTTPException(422,'Etapa não pertence à vaga')
    if stage.id==old.id:return {'ok':True,'unchanged':True}
    reason=str(data.get('reason','')).strip()
    if stage.kind in ('hired','rejected') and len(reason)<3:raise HTTPException(422,'Informe o motivo para decisão final')
    before={'stage':old.name,'status':a.status};a.stage_id=stage.id;a.status='hired' if stage.kind=='hired' else 'rejected' if stage.kind=='rejected' else 'active';a.last_activity_at=now()
    info={'previous':old.name,'next':stage.name,'reason':reason}
    activity(db,user,a.id,'stage_changed',f'{old.name} → {stage.name}'+(f' · {reason}' if reason else ''),info)
    audit(db,user,'stage_changed','application',a.id,before=before,after={'stage':stage.name,'reason':reason})
    process_automation(db,user,a,stage);db.commit();return {'ok':True,'stage':stage.name,'status':a.status,'version':a.version}
@app.post('/api/applications/{application_id}/fit')
def assess_fit(application_id:int,data:dict,user:User=Depends(allowed(*ROLE_EVAL)),db:Session=Depends(get_db)):
    a,c,j,s=get_application(db,user,application_id)
    if 'score' in data:
        score=int(data['score']);reason=str(data.get('reason','')).strip()
        if not 0<=score<=100 or len(reason)<8:raise HTTPException(422,'Nota entre 0 e 100 e justificativa obrigatória')
    else:
        result=ai_service.assess_fit(j.requirements,c.skills+' '+c.resume_text)
        score=result.score;reason=result.explanation
    before={'fit':a.fit,'reason':a.fit_reason};a.fit=score;a.fit_reason=reason;a.last_activity_at=now()
    audit(db,user,'fit_review','application',a.id,before=before,after={'fit':score,'reason':reason});activity(db,user,a.id,'fit_review',f'Fit avaliado: {score}/100')
    db.commit();return {'score':score,'reason':reason,'label':'ALTO FIT' if score>=75 else 'MÉDIO FIT' if score>=50 else 'BAIXO FIT'}

class InterviewIn(BaseModel):
    starts_at:str=Field(min_length=10,max_length=40)
    duration_minutes:int=Field(default=45,ge=15,le=240)
    meeting_link:str=Field(default='',max_length=300)
    notes:str=''
@app.post('/api/applications/{application_id}/interviews')
def create_interview(application_id:int,data:InterviewIn,user:User=Depends(allowed(*ROLE_EVAL)),db:Session=Depends(get_db)):
    a,c,j,s=get_application(db,user,application_id)
    try: datetime.fromisoformat(data.starts_at)
    except ValueError:raise HTTPException(422,'Data inválida')
    interview=Interview(company_id=user.company_id,application_id=a.id,interviewer_id=user.id,**data.model_dump())
    db.add(interview);db.flush();activity(db,user,a.id,'interview',f'Entrevista agendada para {data.starts_at}');audit(db,user,'scheduled','interview',interview.id);db.commit()
    return {'id':interview.id,'status':interview.status}
@app.patch('/api/interviews/{interview_id}')
def update_interview(interview_id:int,data:dict,user:User=Depends(allowed(*ROLE_EVAL)),db:Session=Depends(get_db)):
    it=obj(db,Interview,user,interview_id)
    if not can_access_application(db,user,obj(db,Application,user,it.application_id)):raise HTTPException(403,'Entrevista não atribuída')
    old={'status':it.status,'notes':it.notes}
    if 'status' in data:
        if data['status'] not in ('scheduled','confirmed','completed','canceled','no_show'):raise HTTPException(422,'Status inválido')
        it.status=data['status']
    if 'notes' in data:it.notes=str(data['notes'])[:10000]
    audit(db,user,'updated','interview',it.id,before=old,after={'status':it.status,'notes':it.notes});db.commit();return {'ok':True}
@app.get('/api/interviews')
def interviews(user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    items=db.scalars(select(Interview).where(Interview.company_id==user.company_id,Interview.application_id.in_(accessible_app_ids(db,user))).order_by(Interview.starts_at)).all()
    apps={a.id:a for a in db.scalars(select(Application).where(Application.company_id==user.company_id)).all()}
    candidates={c.id:c for c in db.scalars(select(Candidate).where(Candidate.company_id==user.company_id)).all()}
    return [{'id':i.id,'starts_at':i.starts_at,'status':i.status,'duration_minutes':i.duration_minutes,'application_id':i.application_id,'candidate':candidates[apps[i.application_id].candidate_id].name if i.application_id in apps else '—'} for i in items if i.application_id in apps]

class ScoreCriterion(BaseModel):
    name:str=Field(min_length=2,max_length=80)
    weight:float=Field(default=1,gt=0,le=10)
    score:float=Field(ge=1,le=5)
    comment:str=''
class ScoreIn(BaseModel):criteria:list[ScoreCriterion]=Field(min_length=1,max_length=20);notes:str=''
@app.post('/api/applications/{application_id}/scorecards')
def score(application_id:int,data:ScoreIn,user:User=Depends(allowed(*ROLE_EVAL)),db:Session=Depends(get_db)):
    a,c,j,s=get_application(db,user,application_id)
    value=round(sum(x.score*x.weight for x in data.criteria)/sum(x.weight for x in data.criteria),2)
    sc=Scorecard(company_id=user.company_id,application_id=a.id,author_id=user.id,criteria=[c.model_dump() for c in data.criteria],notes=data.notes,result=value)
    db.add(sc);db.flush();activity(db,user,a.id,'scorecard',f'Scorecard preenchido: {value}/5');audit(db,user,'created','scorecard',sc.id,after={'result':value});db.commit()
    return {'id':sc.id,'result':value}

@app.post('/api/applications/{application_id}/communications')
def send_communication(application_id:int,data:dict,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    a,c,j,s=get_application(db,user,application_id)
    subject=str(data.get('subject','')).strip()[:200];body=str(data.get('body','')).strip()[:10000]
    channel=data.get('channel','email')
    if not subject or not body or channel not in ('email','whatsapp','internal'):raise HTTPException(422,'Assunto, mensagem e canal válidos são obrigatórios')
    # Adapter mock: persists an outbound queue. It does NOT claim external delivery.
    for key,value in {'nome':c.name,'vaga':j.title,'empresa':db.get(Company,user.company_id).name,'recrutador':user.name}.items():
        subject=subject.replace('{{'+key+'}}',value);body=body.replace('{{'+key+'}}',value)
    msg=communications.queue(db,user.company_id,a.id,channel,subject,body)
    db.flush();activity(db,user,a.id,'communication',f'Comunicação {channel} registrada na fila mock');audit(db,user,'queued','communication',msg.id);db.commit()
    return {'id':msg.id,'status':msg.status}

class OfferIn(BaseModel):
    salary:int=Field(gt=0)
    start_date:str=''
    expires_on:str=''
    benefits:str=''
    notes:str=''
@app.post('/api/applications/{application_id}/offers')
def create_offer(application_id:int,data:OfferIn,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    a,c,j,s=get_application(db,user,application_id)
    if a.status=='rejected':raise HTTPException(409,'Não é possível ofertar para candidatura reprovada')
    offer=Offer(company_id=user.company_id,application_id=a.id,token=secrets.token_urlsafe(32),**data.model_dump())
    db.add(offer);db.flush();audit(db,user,'created','offer',offer.id,after={'salary':offer.salary});activity(db,user,a.id,'offer','Proposta gerada como rascunho');db.commit();return {'id':offer.id,'status':offer.status,'accept_path':'/oferta/'+offer.token}
@app.post('/api/offers/{offer_id}/send')
def send_offer(offer_id:int,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    offer=obj(db,Offer,user,offer_id)
    if offer.status not in ('draft','awaiting_approval'):raise HTTPException(409,'Oferta não pode ser enviada neste estado')
    offer.status='sent';audit(db,user,'sent_mock','offer',offer.id);activity(db,user,offer.application_id,'offer','Oferta marcada como enviada (link disponível, sem e-mail externo)');db.commit()
    return {'status':offer.status,'accept_path':'/oferta/'+offer.token}
@app.get('/api/public/offer/{token}')
def public_offer(token:str,db:Session=Depends(get_db)):
    offer=db.scalar(select(Offer).where(Offer.token==token))
    if not offer:raise HTTPException(404,'Oferta não encontrada')
    app_obj=db.get(Application,offer.application_id);job=db.get(Job,app_obj.job_id)
    return {'id':offer.id,'job':job.title,'salary':offer.salary,'benefits':offer.benefits,'start_date':offer.start_date,'expires_on':offer.expires_on,'status':offer.status,'company':db.get(Company,offer.company_id).name}
@app.post('/api/public/offer/{token}/respond')
def respond_offer(token:str,data:dict,request:Request,db:Session=Depends(get_db)):
    rate_limit(db,'offer-response-ip',request.client.host if request.client else 'unknown',40)
    offer=db.scalar(select(Offer).where(Offer.token==token))
    if not offer:raise HTTPException(404,'Oferta não encontrada')
    if offer.status not in ('sent','viewed'):raise HTTPException(409,'Oferta indisponível')
    if offer.expires_on and offer.expires_on<datetime.now().strftime('%Y-%m-%d'):offer.status='expired';db.commit();raise HTTPException(409,'Oferta expirada')
    response=data.get('response')
    if response not in ('accepted','declined'):raise HTTPException(422,'Resposta inválida')
    offer.status=response
    db.add(Activity(company_id=offer.company_id,application_id=offer.application_id,kind='offer_response',description=f'Pessoa candidata respondeu à oferta: {response}'))
    db.add(AuditLog(company_id=offer.company_id,user_id=None,action=response,entity='offer',entity_id=offer.id,after_json={'response':response}))
    db.commit();return {'status':offer.status}

@app.get('/api/offers')
def offers(user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    items=db.scalars(select(Offer).where(Offer.company_id==user.company_id,Offer.application_id.in_(accessible_app_ids(db,user))).order_by(Offer.created_at.desc())).all()
    apps={a.id:a for a in db.scalars(select(Application).where(Application.company_id==user.company_id)).all()}
    cs={c.id:c for c in db.scalars(select(Candidate).where(Candidate.company_id==user.company_id)).all()}
    return [{'id':o.id,'application_id':o.application_id,'candidate':cs[apps[o.application_id].candidate_id].name,'salary':o.salary,'status':o.status,'accept_path':'/oferta/'+o.token} for o in items if o.application_id in apps]

@app.get('/api/dashboard')
def dashboard(user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    job_ids=[j.id for j in db.scalars(select(Job).where(Job.company_id==user.company_id)).all()]
    if user.role not in ('admin','recruiter'):
        permit=accessible_app_ids(db,user)
        apps=db.scalars(select(Application).where(Application.company_id==user.company_id,Application.id.in_(permit))).all()
        job_ids=list(set(a.job_id for a in apps))
    else:apps=db.scalars(select(Application).where(Application.company_id==user.company_id)).all()
    jobs=db.scalars(select(Job).where(Job.company_id==user.company_id,Job.id.in_(job_ids))).all()
    cs={c.id:c for c in db.scalars(select(Candidate).where(Candidate.company_id==user.company_id)).all()}
    stages={s.id:s for s in db.scalars(select(JobStage).where(JobStage.company_id==user.company_id)).all()}
    ints=db.scalars(select(Interview).where(Interview.company_id==user.company_id,Interview.application_id.in_([a.id for a in apps]))).all()
    tasks=db.scalars(select(Task).where(Task.company_id==user.company_id,Task.completed.is_(False),Task.application_id.in_([a.id for a in apps]))).all()
    source_counts=Counter(cs[a.candidate_id].source for a in apps if a.candidate_id in cs)
    stage_counts=Counter(stages[a.stage_id].name for a in apps if a.stage_id in stages)
    hired=[a for a in apps if a.status=='hired']
    delays=[(a.last_activity_at.replace(tzinfo=timezone.utc)-a.created_at.replace(tzinfo=timezone.utc)).days for a in hired]
    today=datetime.now().strftime('%Y-%m-%d')
    return {'metrics':{'jobs_open':sum(j.status=='open' for j in jobs),'jobs_approval':sum(j.status=='approval' for j in jobs),'candidates_active':sum(a.status=='active' for a in apps),'hired':len(hired),'rejected':sum(a.status=='rejected' for a in apps),'interviews':sum(i.status in ('scheduled','confirmed') for i in ints),'avg_time_hire':round(sum(delays)/len(delays),1) if delays else 0,'conversion':round(100*len(hired)/len(apps),1) if apps else 0,'pending_tasks':len(tasks),'late_jobs':sum(1 for j in jobs if j.status=='open' and j.due_date and j.due_date<today)},'sources':[{'name':name,'value':count} for name,count in source_counts.most_common()],'stages':[{'name':name,'value':count} for name,count in stage_counts.most_common()],'by_job':[{'name':j.title,'value':sum(a.job_id==j.id for a in apps)} for j in jobs]}

@app.get('/api/dashboard/trend')
def dashboard_trend(user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    """Candidaturas por mês (data de inscrição) e contratações por mês do último movimento. Só dados reais, no mesmo escopo do painel."""
    if user.role in ('admin','recruiter'):
        apps=db.scalars(select(Application).where(Application.company_id==user.company_id)).all()
    else:
        permit=accessible_app_ids(db,user)
        apps=db.scalars(select(Application).where(Application.company_id==user.company_id,Application.id.in_(permit))).all()
    if not apps:return {'points':[],'total_applications':0,'total_hired':0,'note':'Sem candidaturas para montar a evolução.'}
    now_=datetime.now(timezone.utc)
    def ym(d):
        d=d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d
        return d.year*12+d.month-1
    last=now_.year*12+now_.month-1
    first=max(min(ym(a.created_at) for a in apps),last-11)
    created=Counter(ym(a.created_at) for a in apps if ym(a.created_at)>=first)
    hired=Counter(ym(a.last_activity_at or a.created_at) for a in apps if a.status=='hired' and ym(a.last_activity_at or a.created_at)>=first)
    pts=[{'month':f'{m//12:04d}-{m%12+1:02d}','applications':created.get(m,0),'hired':hired.get(m,0)} for m in range(first,last+1)]
    return {'points':pts,'total_applications':sum(p['applications'] for p in pts),'total_hired':sum(p['hired'] for p in pts),'note':'Contratações são contadas no mês do último movimento da candidatura (a data exata da contratação não é registrada).'}

@app.get('/api/automations')
def automations(user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    rows=db.scalars(select(Automation).where(Automation.company_id==user.company_id)).all()
    return [{'id':a.id,'title':a.title,'trigger':a.trigger,'condition':a.condition_json,'action':a.action_json,'enabled':a.enabled,'runs':a.runs} for a in rows]
@app.post('/api/automations')
def create_automation(data:dict,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    title=str(data.get('title','')).strip()
    if not title:raise HTTPException(422,'Nome obrigatório')
    rule=Automation(company_id=user.company_id,title=title,trigger='stage_changed',condition_json={'stage':str(data.get('stage',''))},action_json={'type':'email','template':str(data.get('subject','Atualização da candidatura'))},enabled=True)
    db.add(rule);db.flush();audit(db,user,'created','automation',rule.id);db.commit();return {'id':rule.id}
@app.post('/api/automations/{automation_id}/toggle')
def toggle_automation(automation_id:int,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    rule=obj(db,Automation,user,automation_id);rule.enabled=not rule.enabled;audit(db,user,'toggled','automation',rule.id,after={'enabled':rule.enabled});db.commit();return {'enabled':rule.enabled}
@app.get('/api/automation-runs')
def automation_runs(user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    rows=db.scalars(select(AutomationRun).where(AutomationRun.company_id==user.company_id).order_by(AutomationRun.created_at.desc()).limit(70)).all()
    return [{'id':v.id,'automation_id':v.automation_id,'status':v.status,'detail':v.detail,'at':v.created_at.isoformat()} for v in rows]
@app.get('/api/tasks')
def tasks(user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    ts=db.scalars(select(Task).where(Task.company_id==user.company_id,Task.application_id.in_(accessible_app_ids(db,user))).order_by(Task.completed,Task.due_date)).all()
    return [{'id':t.id,'title':t.title,'completed':t.completed,'due_date':t.due_date,'application_id':t.application_id} for t in ts]
@app.post('/api/tasks/{task_id}/toggle')
def toggle_task(task_id:int,user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    task=obj(db,Task,user,task_id)
    if task.application_id not in accessible_app_ids(db,user):raise HTTPException(403,'Tarefa não atribuída')
    task.completed=not task.completed;audit(db,user,'toggled','task',task.id);db.commit();return {'completed':task.completed}
@app.get('/api/tests')
def test_defs(user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    rows=db.scalars(select(TestDefinition).where(TestDefinition.company_id==user.company_id)).all()
    return [{'id':t.id,'title':t.title,'questions':t.questions,'duration_minutes':t.duration_minutes,'pass_percent':t.pass_percent} for t in rows]
@app.post('/api/tests')
def create_test(data:dict,user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    title=str(data.get('title','')).strip();questions=data.get('questions')
    if not title or not isinstance(questions,list) or not questions:raise HTTPException(422,'Nome e questões obrigatórios')
    t=TestDefinition(company_id=user.company_id,title=title[:120],questions=questions[:50],duration_minutes=int(data.get('duration_minutes',30)),pass_percent=int(data.get('pass_percent',70)));db.add(t);db.flush();audit(db,user,'created','test',t.id);db.commit();return {'id':t.id}
@app.get('/api/audit')
def audits(user:User=Depends(allowed('admin')),db:Session=Depends(get_db)):
    rows=db.scalars(select(AuditLog).where(AuditLog.company_id==user.company_id).order_by(AuditLog.created_at.desc()).limit(150)).all()
    return [{'action':r.action,'entity':r.entity,'entity_id':r.entity_id,'user_id':r.user_id,'at':r.created_at.isoformat()} for r in rows]
@app.get('/api/reports')
def reports(user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    return dashboard(user,db)

@app.get('/api/public/jobs')
def public_jobs(request:Request,company:str='',db:Session=Depends(get_db)):
    """Página de carreiras. Na v1 é POR EMPRESA (slug obrigatório): uma empresa não vê as vagas das outras.
    O caminho legado /api/public/jobs sem filtro continua só para a interface v1.1 de desenvolvimento."""
    stmt=select(Job).where(Job.status=='open').order_by(Job.created_at.desc())
    if request.url.path.startswith('/api/v1/'):
        if not company.strip():raise HTTPException(422,'Informe a empresa (parâmetro company)')
        owner=db.scalar(select(Company).where(Company.slug==company.strip().lower()))
        if not owner:return []
        stmt=stmt.where(Job.company_id==owner.id)
    elif company.strip():
        owner=db.scalar(select(Company).where(Company.slug==company.strip().lower()))
        stmt=stmt.where(Job.company_id==(owner.id if owner else -1))
    rows=db.scalars(stmt).all()
    names={c.id:c.name for c in db.scalars(select(Company)).all()}
    return [{'id':j.id,'title':j.title,'company':names.get(j.company_id,''),'location':j.location,'modality':j.modality,'department':j.department,'description':j.description,'requirements':j.requirements,'benefits':j.benefits} for j in rows]
class PublicApply(BaseModel):
    job_id:int
    name:str=Field(min_length=3,max_length=200)
    email:EmailStr
    phone:str=''
    location:str=''
    resume_text:str=''
    consent:bool
@app.post('/api/public/apply')
def public_apply(data:PublicApply,request:Request,db:Session=Depends(get_db)):
    rate_limit(db,'public-apply-ip',request.client.host if request.client else 'unknown',25)
    j=db.get(Job,data.job_id)
    if not j or j.status!='open':raise HTTPException(404,'Vaga não disponível')
    if not data.consent:raise HTTPException(422,'Consentimento de tratamento de dados obrigatório')
    # Prevent duplicate candidacies to same job; do not disclose existence of email on public interface.
    candidate=db.scalar(select(Candidate).where(Candidate.company_id==j.company_id,Candidate.email==data.email.lower(),Candidate.deleted.is_(False)))
    if not candidate:
        candidate=Candidate(company_id=j.company_id,name=data.name,email=data.email.lower(),phone=data.phone,location=data.location,resume_text=data.resume_text,source='Página de carreiras',consent=True)
        db.add(candidate);db.flush()
    existing=db.scalar(select(Application).where(Application.company_id==j.company_id,Application.candidate_id==candidate.id,Application.job_id==j.id))
    if not existing:
        stage=db.scalar(select(JobStage).where(JobStage.company_id==j.company_id,JobStage.job_id==j.id).order_by(JobStage.order))
        a=Application(company_id=j.company_id,job_id=j.id,candidate_id=candidate.id,stage_id=stage.id,fit=50)
        db.add(a);db.flush();db.add(Activity(company_id=j.company_id,application_id=a.id,kind='application',description='Inscrição recebida pela página de carreiras'))
        db.add(AuditLog(company_id=j.company_id,action='public_application',entity='application',entity_id=a.id))
    db.commit();return {'ok':True,'message':'Candidatura recebida. Obrigado pelo interesse!'}

def parse_resume(filename: str,content: bytes)->str:
    suffix=Path(filename).suffix.lower()
    if suffix=='.pdf':
        import fitz
        with fitz.open(stream=content,filetype='pdf') as doc:
            return '\n'.join(p.get_text() for p in doc[:50])[:100000]
    if suffix=='.docx':
        from docx import Document
        doc=Document(io.BytesIO(content))
        return '\n'.join(p.text for p in doc.paragraphs)[:100000]
    if suffix=='.doc':
        with tempfile.NamedTemporaryFile(suffix='.doc') as temp:
            temp.write(content);temp.flush()
            process=subprocess.run(['antiword',temp.name],capture_output=True,text=True,timeout=10)
        if process.returncode!=0:raise HTTPException(422,'Não foi possível interpretar o arquivo DOC')
        return process.stdout[:100000]
    raise HTTPException(422,'Formato não suportado')

@app.post('/api/candidates/{candidate_id}/resume')
async def upload_resume(candidate_id:int,file:UploadFile=File(...),user:User=Depends(allowed(*ROLE_EDIT)),db:Session=Depends(get_db)):
    c=obj(db,Candidate,user,candidate_id)
    suffix=Path(file.filename or '').suffix.lower()
    if suffix not in ('.pdf','.doc','.docx'):raise HTTPException(422,'Envie PDF, DOC ou DOCX')
    content=await file.read(5*1024*1024+1)
    if len(content)>5*1024*1024:raise HTTPException(413,'Limite de 5 MB por currículo')
    if not content:raise HTTPException(422,'Arquivo vazio')
    if suffix=='.pdf' and not content.startswith(b'%PDF-'):
        raise HTTPException(422,'Arquivo PDF inválido')
    if suffix=='.doc' and not content.startswith(bytes.fromhex('D0CF11E0A1B11AE1')):
        raise HTTPException(422,'Arquivo DOC inválido')
    if suffix=='.docx':
        import zipfile
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                entries=archive.infolist()
                if len(entries)>1500 or sum(e.file_size for e in entries)>25*1024*1024 or 'word/document.xml' not in archive.namelist():
                    raise HTTPException(422,'Estrutura DOCX inválida ou excessiva')
        except zipfile.BadZipFile:raise HTTPException(422,'DOCX corrompido')
    try:raw=parse_resume(file.filename,content)
    except HTTPException:raise
    except Exception:raise HTTPException(422,'Currículo ilegível ou corrompido')
    fname=Path(file.filename).name[:180]
    storage_key=secrets.token_hex(20)+suffix
    LocalPrivateStorage(ROOT/'private_uploads').store(user.company_id,storage_key,content)
    detected_email=re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',raw)
    detected_phone=re.findall(r'(?:\+55\s*)?\(?\d{2}\)?\s*9?\d{4}[-\s]?\d{4}',raw)
    metadata={'email':detected_email[0] if detected_email else None,'phone':detected_phone[0] if detected_phone else None}
    resume=Resume(company_id=user.company_id,candidate_id=c.id,filename=fname,mime_type={'pdf':'application/pdf','doc':'application/msword','docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}[suffix.lstrip('.')],storage_key=storage_key,sha256=hashlib.sha256(content).hexdigest(),extracted_text=raw,metadata_json=metadata)
    db.add(resume)
    if raw.strip():c.resume_text=raw
    audit(db,user,'uploaded','resume',c.id,after={'filename':fname,'sha256':resume.sha256});db.commit()
    return {'id':resume.id,'filename':fname,'extracted_chars':len(raw),'detected':metadata}

@app.get('/api/candidates/{candidate_id}/resumes')
def list_resumes(candidate_id:int,user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    c=obj(db,Candidate,user,candidate_id)
    if user.role not in ('admin','recruiter') and not any(a.candidate_id==candidate_id for a in db.scalars(select(Application).where(Application.id.in_(accessible_app_ids(db,user)))).all()):raise HTTPException(403,'Sem acesso ao documento')
    items=db.scalars(select(Resume).where(Resume.company_id==user.company_id,Resume.candidate_id==c.id).order_by(Resume.created_at.desc())).all()
    return [{'id':r.id,'filename':r.filename,'created_at':r.created_at.isoformat(),'text_chars':len(r.extracted_text)} for r in items]

@app.get('/api/resumes/{resume_id}/download')
def download_resume(resume_id:int,user:User=Depends(allowed(*ROLE_VIEW)),db:Session=Depends(get_db)):
    r=obj(db,Resume,user,resume_id)
    if user.role not in ('admin','recruiter') and not any(a.candidate_id==r.candidate_id for a in db.scalars(select(Application).where(Application.id.in_(accessible_app_ids(db,user)))).all()):raise HTTPException(403,'Sem acesso ao documento')
    target=ROOT/'private_uploads'/str(user.company_id)/r.storage_key
    if not target.exists():raise HTTPException(404,'Arquivo original indisponível')
    return FileResponse(target,filename=r.filename,media_type=r.mime_type)


@app.post('/api/jobs/{job_id}/approve')
def approve_job(job_id:int,data:dict,user:User=Depends(allowed('admin','manager')),db:Session=Depends(get_db)):
    job=obj(db,Job,user,job_id)
    if user.role=='manager' and job.manager_id!=user.id:raise HTTPException(403,'Sem atribuição à vaga')
    if job.status!='approval':raise HTTPException(409,'Vaga não está pendente de aprovação')
    decision=data.get('decision')
    if decision not in ('approved','rejected'):raise HTTPException(422,'Decisão inválida')
    job.status='open' if decision=='approved' else 'closed'
    db.add(JobApproval(company_id=user.company_id,job_id=job.id,approver_id=user.id,status=decision,comment=str(data.get('comment',''))[:3000]))
    audit(db,user,'job_approval','job',job.id,before={'status':'approval'},after={'status':job.status,'decision':decision})
    db.commit();return {'status':job.status}

@app.post('/api/candidates/{candidate_id}/anonymize')
def anonymize_candidate(candidate_id:int,user:User=Depends(allowed('admin')),db:Session=Depends(get_db)):
    c=obj(db,Candidate,user,candidate_id)
    for field in ('name','email','phone','location','title','source','skills','education','resume_text'):
        setattr(c,field,'Anonimizado' if field=='name' else '')
    c.experience_years=0;c.consent=False;c.deleted=True
    for resume in db.scalars(select(Resume).where(Resume.company_id==user.company_id,Resume.candidate_id==c.id)).all():
        target=ROOT/'private_uploads'/str(user.company_id)/resume.storage_key
        try:target.unlink(missing_ok=True)
        except OSError:pass
        db.delete(resume)
    audit(db,user,'anonymized','candidate',candidate_id,after={'deleted':True})
    db.commit();return {'anonymized':True}

@app.get('/api/health')
def health():return {'status':'ok','product':'TalentFlow ATS'}

# ---- API v1: mesmas regras de negócio/RBAC, caminho versionado, OpenAPI limpo ----------
# As rotas legadas /api/* continuam funcionando para a interface v1.1 (sem quebra abrupta)
# mas saem do OpenAPI; clientes novos usam exclusivamente /api/v1/*.
_LEGACY_ONLY=('/api/auth/','/api/me','/api/health','/api/workspace','/api/docs','/api/openapi')
for _r in list(app.router.routes):
    _path=getattr(_r,'path','')
    if _path.startswith(_LEGACY_ONLY):_r.include_in_schema=False
    if not _path.startswith('/api/') or _path.startswith('/api/v1/') or _path.startswith(_LEGACY_ONLY):continue
    app.add_api_route('/api/v1'+_path[4:],_r.endpoint,methods=sorted(_r.methods),name=_r.name+'_v1',
        tags=list(_r.tags or [])+['v1'],response_model=getattr(_r,'response_model',None),
        status_code=getattr(_r,'status_code',None),dependencies=getattr(_r,'dependencies',None),summary=_r.summary)
    _r.include_in_schema=False

# Interface legada v1.1 (somente desenvolvimento): em produção o site é o pacote compilado
# do apps/web, servido pelo servidor do proprietário; a API não entrega HTML.
if os.getenv('APP_ENV','development').lower()!='production' and os.getenv('SERVE_LEGACY_WEB','true').lower()=='true':
    app.mount('/assets',StaticFiles(directory=ROOT/'web'),name='assets')
    @app.get('/workspace',include_in_schema=False)
    def connected_workspace(user:User=Depends(allowed('admin'))):
        # Personal data is never embedded in an unauthenticated route.
        return FileResponse(ROOT/'private_views'/'workspace.html',headers={'Cache-Control':'no-store'})

    @app.get('/{path:path}',include_in_schema=False)
    def frontend(path:str):
        return FileResponse(ROOT/'web'/'index.html')
