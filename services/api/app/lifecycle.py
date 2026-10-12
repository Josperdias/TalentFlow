"""TalentFlow People API: measurable employee lifecycle. Evidence != predictive validity.

All reads/writes scope to the authenticated tenant AND validate cross-record tenant refs.
Metrics carry numerators, denominators, interpretation and data limitations.
"""
from collections import Counter
from datetime import date,datetime,timedelta,timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel,EmailStr,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import get_db
from .security import allowed,current_user
from .models import (User,Employee,OnboardingItem,LearningCourse,LearningEnrollment,
    PerformanceGoal,PerformanceReview,CareerEvent,Application,Job,Candidate,Offer,AuditLog)

router=APIRouter(prefix='/lifecycle',tags=['People Lifecycle'])
ALL_ROLES=('admin','recruiter','manager')
WRITERS=('admin','recruiter')

def locate(db,model,user,id):
    x=db.scalar(select(model).where(model.company_id==user.company_id,model.id==id))
    if not x:raise HTTPException(404,'Registro não encontrado')
    return x

def person(db,user,id):
    x=locate(db,Employee,user,id)
    if user.role=='manager' and x.manager_id!=user.id:raise HTTPException(403,'Colaborador não atribuído')
    return x

def records(db,model,user):
    return db.scalars(select(model).where(model.company_id==user.company_id)).all()

def log(db,user,action,entity,item_id,before=None,after=None):
    db.add(AuditLog(company_id=user.company_id,user_id=user.id,action=action,entity=entity,entity_id=item_id,before_json=before or {},after_json=after or {}))

def valid_date(value):
    try:return date.fromisoformat(value)
    except (ValueError,TypeError):raise HTTPException(422,'Data inválida (AAAA-MM-DD)')

def employee_json(e):
    return {'id':e.id,'name':e.name,'employee_code':e.employee_code,'work_email':e.work_email,'department':e.department,'job_title':e.job_title,'hire_date':e.hire_date,'exit_date':e.exit_date,'exit_kind':e.exit_kind,'status':e.status,'application_id':e.application_id,'manager_id':e.manager_id}

class NewEmployee(BaseModel):
    name:str=Field(min_length=2,max_length=200)
    work_email:EmailStr
    department:str=Field(default='Pessoas',max_length=100)
    job_title:str=Field(default='',max_length=160)
    hire_date:str
    manager_id:int|None=None

@router.get('/employees')
def employees(user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    people=records(db,Employee,user)
    if user.role=='manager':people=[p for p in people if p.manager_id==user.id]
    return [employee_json(e) for e in sorted(people,key=lambda e:e.name)]

@router.post('/employees')
def create_employee(data:NewEmployee,user:User=Depends(allowed(*WRITERS)),db:Session=Depends(get_db)):
    valid_date(data.hire_date)
    if data.manager_id:locate(db,User,user,data.manager_id)
    last=db.scalars(select(Employee.id).where(Employee.company_id==user.company_id).order_by(Employee.id.desc()).limit(1)).first() or 0
    e=Employee(company_id=user.company_id,employee_code=f'COL-{last+1:05}',name=data.name,work_email=str(data.work_email).lower(),department=data.department,job_title=data.job_title,hire_date=data.hire_date,manager_id=data.manager_id)
    db.add(e);db.flush();log(db,user,'employee_created','employee',e.id,after=employee_json(e));db.commit();return employee_json(e)

@router.post('/from-application/{application_id}')
def convert_from_hire(application_id:int,user:User=Depends(allowed(*WRITERS)),db:Session=Depends(get_db)):
    a=locate(db,Application,user,application_id)
    if a.status!='hired':raise HTTPException(409,'Candidatura ainda não foi contratada')
    if db.scalar(select(Employee.id).where(Employee.company_id==user.company_id,Employee.application_id==a.id)):raise HTTPException(409,'Colaborador já integrado')
    accepted=db.scalar(select(Offer.id).where(Offer.company_id==user.company_id,Offer.application_id==a.id,Offer.status=='accepted'))
    if not accepted:raise HTTPException(409,'É necessária uma proposta aceita para integrar a contratação')
    c=locate(db,Candidate,user,a.candidate_id);j=locate(db,Job,user,a.job_id)
    last=db.scalars(select(Employee.id).where(Employee.company_id==user.company_id).order_by(Employee.id.desc()).limit(1)).first() or 0
    e=Employee(company_id=user.company_id,employee_code=f'COL-{last+1:05}',name=c.name,work_email=c.email,department=j.department,job_title=j.title,hire_date=date.today().isoformat(),application_id=a.id,manager_id=j.manager_id)
    db.add(e);db.flush()
    for phase,title,days in DEFAULT_CHECKLIST:
        db.add(OnboardingItem(company_id=user.company_id,employee_id=e.id,title=title,phase=phase,due_date=(date.today()+timedelta(days=days)).isoformat()))
    log(db,user,'candidate_to_employee','employee',e.id,after=employee_json(e));db.commit();return employee_json(e)

DEFAULT_CHECKLIST=[('Pré-admissão','Validar dados e documentos',0),('Dia 1','Boas-vindas e apresentação ao time',1),('Primeira semana','Liberar acessos e equipamentos',5),('Primeiro mês','Alinhar objetivos e expectativas',30),('Primeiros 90 dias','Realizar conversa de acompanhamento',90)]

@router.get('/employees/{employee_id}')
def employee_detail(employee_id:int,user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    e=person(db,user,employee_id)
    tasks=db.scalars(select(OnboardingItem).where(OnboardingItem.company_id==user.company_id,OnboardingItem.employee_id==e.id).order_by(OnboardingItem.id)).all()
    enrollments=db.scalars(select(LearningEnrollment).where(LearningEnrollment.company_id==user.company_id,LearningEnrollment.employee_id==e.id)).all()
    goals=db.scalars(select(PerformanceGoal).where(PerformanceGoal.company_id==user.company_id,PerformanceGoal.employee_id==e.id)).all()
    reviews=db.scalars(select(PerformanceReview).where(PerformanceReview.company_id==user.company_id,PerformanceReview.employee_id==e.id)).all()
    courses={c.id:c for c in records(db,LearningCourse,user)}
    events=db.scalars(select(CareerEvent).where(CareerEvent.company_id==user.company_id,CareerEvent.employee_id==e.id).order_by(CareerEvent.effective_on.desc())).all()
    return {'employee':employee_json(e),'onboarding':[{'id':t.id,'phase':t.phase,'title':t.title,'due_date':t.due_date,'done':bool(t.completed_at)} for t in tasks],
        'learning':[{'id':a.id,'course':courses[a.course_id].title,'status':a.status,'assigned_at':a.assigned_at,'completed_at':a.completed_at} for a in enrollments if a.course_id in courses],
        'goals':[{'id':g.id,'title':g.title,'target':g.target_value,'actual':g.actual_value,'unit':g.metric_unit,'due_date':g.due_date,'status':g.status} for g in goals],
        'reviews':[{'id':r.id,'period':r.period,'score':r.score,'criteria':r.criteria,'feedback':r.feedback} for r in reviews],
        'career':[{'id':v.id,'kind':v.kind,'description':v.description,'date':v.effective_on} for v in events]}

class OnboardIn(BaseModel):
    title:str=Field(min_length=2,max_length=160)
    phase:str=Field(default='Primeiro mês',max_length=40)
    due_date:str|None=None

@router.post('/employees/{employee_id}/onboarding')
def add_onboarding(employee_id:int,data:OnboardIn,user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    person(db,user,employee_id)
    if data.due_date:valid_date(data.due_date)
    t=OnboardingItem(company_id=user.company_id,employee_id=employee_id,**data.model_dump());db.add(t);db.flush();log(db,user,'onboarding_created','onboarding_item',t.id);db.commit();return {'id':t.id,'done':False}

@router.post('/onboarding/{item_id}/toggle')
def toggle_onboarding(item_id:int,user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    item=locate(db,OnboardingItem,user,item_id);person(db,user,item.employee_id)
    previous=bool(item.completed_at)
    item.completed_at=None if previous else datetime.now(timezone.utc)
    log(db,user,'onboarding_updated','onboarding_item',item.id,before={'done':previous},after={'done':not previous});db.commit();return {'id':item.id,'done':not previous}

@router.get('/courses')
def courses(user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    return [{'id':c.id,'title':c.title,'skill':c.skill,'duration_hours':c.duration_hours,'enrollments':db.query(LearningEnrollment).filter_by(company_id=user.company_id,course_id=c.id).count()} for c in records(db,LearningCourse,user)]

class CourseIn(BaseModel):
    title:str=Field(min_length=3,max_length=160)
    skill:str=Field(default='',max_length=120)
    duration_hours:float=Field(gt=0,le=10000,default=2)

@router.post('/courses')
def create_course(data:CourseIn,user:User=Depends(allowed(*WRITERS)),db:Session=Depends(get_db)):
    c=LearningCourse(company_id=user.company_id,**data.model_dump());db.add(c);db.flush();log(db,user,'course_created','learning_course',c.id);db.commit();return {'id':c.id,'title':c.title}

class EnrollmentIn(BaseModel):
    employee_id:int
    course_id:int

@router.post('/enrollments')
def assign_course(data:EnrollmentIn,user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    person(db,user,data.employee_id);locate(db,LearningCourse,user,data.course_id)
    existing=db.scalar(select(LearningEnrollment).where(LearningEnrollment.company_id==user.company_id,LearningEnrollment.employee_id==data.employee_id,LearningEnrollment.course_id==data.course_id))
    if existing:raise HTTPException(409,'Curso já atribuído')
    a=LearningEnrollment(company_id=user.company_id,employee_id=data.employee_id,course_id=data.course_id,assigned_at=date.today().isoformat());db.add(a);db.flush();log(db,user,'learning_assigned','learning_enrollment',a.id);db.commit();return {'id':a.id,'status':a.status}

@router.post('/enrollments/{id}/complete')
def complete_course(id:int,user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    a=locate(db,LearningEnrollment,user,id);person(db,user,a.employee_id)
    a.status='completed';a.completed_at=date.today().isoformat();log(db,user,'learning_completed','learning_enrollment',a.id);db.commit();return {'id':a.id,'status':'completed'}

class GoalIn(BaseModel):
    title:str=Field(min_length=3,max_length=200)
    target_value:float=Field(gt=0)
    actual_value:float=Field(ge=0,default=0)
    metric_unit:str=Field(default='unidades',max_length=40)
    due_date:str

@router.post('/employees/{employee_id}/goals')
def add_goal(employee_id:int,data:GoalIn,user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    person(db,user,employee_id);valid_date(data.due_date)
    g=PerformanceGoal(company_id=user.company_id,employee_id=employee_id,**data.model_dump());db.add(g);db.flush();log(db,user,'goal_created','performance_goal',g.id);db.commit();return {'id':g.id}

class ProgressIn(BaseModel):
    actual_value:float=Field(ge=0)

@router.post('/goals/{goal_id}/progress')
def update_goal(goal_id:int,data:ProgressIn,user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    g=locate(db,PerformanceGoal,user,goal_id);person(db,user,g.employee_id);previous=g.actual_value
    g.actual_value=data.actual_value;g.status='achieved' if g.actual_value>=g.target_value else 'active'
    log(db,user,'goal_progress','performance_goal',g.id,before={'actual':previous},after={'actual':g.actual_value});db.commit();return {'id':g.id,'status':g.status}

class ReviewIn(BaseModel):
    period:str=Field(min_length=4,max_length=30)
    criteria:list[dict]=Field(min_length=1,max_length=20)
    feedback:str=Field(default='',max_length=3000)

@router.post('/employees/{employee_id}/reviews')
def create_review(employee_id:int,data:ReviewIn,user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    person(db,user,employee_id)
    try:
        vals=[(float(x['score']),float(x.get('weight',1))) for x in data.criteria]
        if any(not(1<=s<=5 and 0<w<=100) for s,w in vals):raise ValueError()
    except (KeyError,TypeError,ValueError):raise HTTPException(422,'Critérios exigem notas de 1 a 5 e pesos positivos')
    result=round(sum(s*w for s,w in vals)/sum(w for s,w in vals),2)
    r=PerformanceReview(company_id=user.company_id,employee_id=employee_id,reviewer_id=user.id,period=data.period,criteria=data.criteria,score=result,feedback=data.feedback)
    db.add(r);db.flush();log(db,user,'performance_review_created','performance_review',r.id,after={'score':result});db.commit();return {'id':r.id,'score':result,'note':'Pontuação descritiva; não constitui instrumento psicometricamente validado.'}

class CareerIn(BaseModel):
    kind:str
    description:str=Field(min_length=4,max_length=1000)
    effective_on:str

@router.post('/employees/{employee_id}/career')
def career_event(employee_id:int,data:CareerIn,user:User=Depends(allowed(*WRITERS)),db:Session=Depends(get_db)):
    person(db,user,employee_id);valid_date(data.effective_on)
    if data.kind not in ('promotion','transfer','recognition','other','exit'):raise HTTPException(422,'Evento inválido')
    v=CareerEvent(company_id=user.company_id,employee_id=employee_id,**data.model_dump());db.add(v);db.flush();log(db,user,'career_event','career_event',v.id);db.commit();return {'id':v.id}

class ExitIn(BaseModel):
    exit_date:str
    kind:str

@router.post('/employees/{employee_id}/exit')
def exit_employee(employee_id:int,data:ExitIn,user:User=Depends(allowed(*WRITERS)),db:Session=Depends(get_db)):
    e=person(db,user,employee_id);exit_day=valid_date(data.exit_date)
    if exit_day<valid_date(e.hire_date):raise HTTPException(422,'Saída anterior à admissão')
    if data.kind not in ('voluntary','involuntary','other'):raise HTTPException(422,'Motivo inválido')
    if e.status=='exited':raise HTTPException(409,'Desligamento já registrado')
    e.status='exited';e.exit_date=data.exit_date;e.exit_kind=data.kind
    log(db,user,'employee_exit','employee',e.id,after={'exit_date':e.exit_date,'kind':e.exit_kind});db.commit();return employee_json(e)

def measure(value,numerator,denominator,description,method,minimum_n=0):
    return {'value':None if denominator<minimum_n else value,'numerator':numerator,'denominator':denominator,
        'description':description,'method':method,'suppressed':denominator<minimum_n}

@router.get('/analytics')
def analytics(user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    today=date.today();cutoff=today-timedelta(days=365);at90=today-timedelta(days=90)
    ps=records(db,Employee,user)
    if user.role=='manager':ps=[e for e in ps if e.manager_id==user.id]
    ids={e.id for e in ps}
    tasks=[t for t in records(db,OnboardingItem,user) if t.employee_id in ids]
    enroll=[a for a in records(db,LearningEnrollment,user) if a.employee_id in ids]
    goals=[g for g in records(db,PerformanceGoal,user) if g.employee_id in ids]
    active=[e for e in ps if e.status=='active']
    exits=[e for e in ps if e.exit_date and valid_date(e.exit_date)>=cutoff and e.exit_kind=='voluntary']
    opened=[e for e in ps if valid_date(e.hire_date)<=cutoff and (not e.exit_date or valid_date(e.exit_date)>cutoff)]
    closed=[e for e in ps if valid_date(e.hire_date)<=today and (not e.exit_date or valid_date(e.exit_date)>today)]
    average=(len(opened)+len(closed))/2
    cohort=[e for e in ps if valid_date(e.hire_date)<=at90]
    retained=sum(1 for e in cohort if not e.exit_date or valid_date(e.exit_date)>=valid_date(e.hire_date)+timedelta(days=90))
    done_tasks=sum(bool(t.completed_at) for t in tasks)
    learned=sum(a.status=='completed' for a in enroll)
    reached=sum(g.actual_value>=g.target_value for g in goals)
    stages=Counter(e.department for e in active)
    return {'as_of':today.isoformat(),'scope':'empresa' if user.role!='manager' else 'equipe atribuída','indicators':{
        'active_headcount':measure(len(active),len(active),len(ps),'Colaboradores com vínculo ativo','Contagem de vínculos ativos. Operacional.'),
        'onboarding_completion':measure(round(done_tasks/len(tasks)*100,1) if tasks else None,done_tasks,len(tasks),'Conclusão de atividades de integração (%)','Tarefas concluídas / tarefas cadastradas; não mede adaptação nem qualidade.'),
        'learning_completion':measure(round(learned/len(enroll)*100,1) if enroll else None,learned,len(enroll),'Conclusão de inscrições de aprendizagem (%)','Cursos concluídos / cursos atribuídos; não mede transferência ao trabalho.'),
        'goal_attainment':measure(round(reached/len(goals)*100,1) if goals else None,reached,len(goals),'Metas quantitativas alcançadas (%)','Metas com resultado >= alvo / metas cadastradas; depende da qualidade de definição das metas.'),
        'voluntary_turnover_12m':measure(round(len(exits)/average*100,1) if average else None,len(exits),round(average,1),'Rotatividade voluntária estimada nos últimos 365 dias (%)','Desligamentos voluntários / média entre efetivos estimados no início e fim do período; não substitui média mensal.'),
        'retention_90d':measure(round(retained/len(cohort)*100,1) if cohort else None,retained,len(cohort),'Retenção aos 90 dias (%)','Admitidos há >=90 dias que permaneceram ao menos 90 dias / coorte elegível.',minimum_n=5),
    },'departments':[{'name':n,'value':v} for n,v in stages.most_common()],
    'evidence_note':'Taxas acima são métricas descritivas de gestão, não instrumentos científicos validados. Referência de categorização: ISO 30414:2025. Interpretar com base no denominador, contexto, qualidade e decisões humanas.'}

@router.get('/onboarding')
def onboarding_overview(user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    employees={e.id:e for e in records(db,Employee,user) if user.role!='manager' or e.manager_id==user.id}
    return [{'id':t.id,'employee_id':t.employee_id,'employee':employees[t.employee_id].name,'title':t.title,'phase':t.phase,'due_date':t.due_date,'done':bool(t.completed_at)} for t in records(db,OnboardingItem,user) if t.employee_id in employees]

@router.get('/enrollments')
def learning_overview(user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    employees={e.id:e for e in records(db,Employee,user) if user.role!='manager' or e.manager_id==user.id}
    courses={c.id:c for c in records(db,LearningCourse,user)}
    return [{'id':a.id,'employee_id':a.employee_id,'employee':employees[a.employee_id].name,'course_id':a.course_id,'course':courses[a.course_id].title,'status':a.status,'assigned_at':a.assigned_at,'completed_at':a.completed_at} for a in records(db,LearningEnrollment,user) if a.employee_id in employees and a.course_id in courses]

@router.get('/goals')
def goals_overview(user:User=Depends(allowed(*ALL_ROLES)),db:Session=Depends(get_db)):
    employees={e.id:e for e in records(db,Employee,user) if user.role!='manager' or e.manager_id==user.id}
    return [{'id':g.id,'employee_id':g.employee_id,'employee':employees[g.employee_id].name,'title':g.title,'unit':g.metric_unit,'target':g.target_value,'actual':g.actual_value,'due_date':g.due_date,'status':g.status} for g in records(db,PerformanceGoal,user) if g.employee_id in employees]
