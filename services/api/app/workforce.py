"""TalentFlow workforce workflows: auditable PDIs, leave requests and useful aggregates.
Patterns influenced by Frappe HR/Horilla; this is original implementation, no GPL code.
"""
from datetime import date,datetime,timezone,timedelta
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Literal
from .database import get_db
from .security import allowed
from .models import User, Employee, DevelopmentPlan, LeaveRequest, AuditLog

router=APIRouter(prefix='/api/workforce',tags=['Workforce'])
ROLES=('admin','recruiter','manager')


def scoped(db,model,user,id):
    record=db.scalar(select(model).where(model.id==id,model.company_id==user.company_id))
    if not record:raise HTTPException(404,'Registro não encontrado')
    return record

def employee_scoped(db,user,id):
    e=scoped(db,Employee,user,id)
    if user.role=='manager' and e.manager_id!=user.id:raise HTTPException(403,'Colaborador fora de sua equipe')
    return e

def log(db,user,action,entity,item_id,before=None,after=None):
    db.add(AuditLog(company_id=user.company_id,user_id=user.id,action=action,entity=entity,entity_id=item_id,before_json=before or {},after_json=after or {}))

def iso(value):
    try:return date.fromisoformat(value)
    except (ValueError,TypeError):raise HTTPException(422,'Informe data no formato AAAA-MM-DD')

def plan_json(x,employee):
    return {'id':x.id,'employee_id':employee.id,'employee':employee.name,'title':x.title,'competency':x.competency,'goal':x.goal,'actions':x.actions,'progress':x.progress,'status':x.status,'due_date':x.due_date,'owner_id':x.owner_id}

class PlanIn(BaseModel):
    employee_id:int
    title:str=Field(min_length=3,max_length=180)
    competency:str=Field(default='',max_length=140)
    goal:str=Field(min_length=6,max_length=3000)
    due_date:str
    actions:list[str]=Field(min_length=1,max_length=12)

@router.get('/plans')
def plans(employee_id:int|None=None,status:str='',user:User=Depends(allowed(*ROLES)),db:Session=Depends(get_db)):
    people={e.id:e for e in db.scalars(select(Employee).where(Employee.company_id==user.company_id)).all() if user.role!='manager' or e.manager_id==user.id}
    stmt=select(DevelopmentPlan).where(DevelopmentPlan.company_id==user.company_id,DevelopmentPlan.employee_id.in_(list(people)))
    if employee_id is not None:stmt=stmt.where(DevelopmentPlan.employee_id==employee_id)
    if status:stmt=stmt.where(DevelopmentPlan.status==status)
    return [plan_json(p,people[p.employee_id]) for p in db.scalars(stmt.order_by(DevelopmentPlan.created_at.desc())).all()]

@router.post('/plans')
def create_plan(data:PlanIn,user:User=Depends(allowed(*ROLES)),db:Session=Depends(get_db)):
    e=employee_scoped(db,user,data.employee_id)
    deadline=iso(data.due_date)
    if deadline < date.today()-timedelta(days=365):raise HTTPException(422,'Prazo anterior ao período permitido')
    actions=[{'title':a.strip(),'done':False,'evidence':''} for a in data.actions if isinstance(a,str) and 3<=len(a.strip())<=240]
    if len(actions)!=len(data.actions):raise HTTPException(422,'Cada atividade deve conter entre 3 e 240 caracteres')
    p=DevelopmentPlan(company_id=user.company_id,employee_id=e.id,title=data.title,competency=data.competency,goal=data.goal,due_date=data.due_date,actions=actions,owner_id=user.id)
    db.add(p);db.flush();log(db,user,'development_plan_created','development_plan',p.id,after={'employee_id':e.id,'title':p.title,'actions':len(actions)})
    db.commit();return plan_json(p,e)

class PlanAction(BaseModel):
    index:int=Field(ge=0,le=11)
    done:bool
    evidence:str=Field(default='',max_length=1000)

@router.post('/plans/{plan_id}/action')
def update_plan_action(plan_id:int,data:PlanAction,user:User=Depends(allowed(*ROLES)),db:Session=Depends(get_db)):
    p=scoped(db,DevelopmentPlan,user,plan_id);e=employee_scoped(db,user,p.employee_id)
    if p.status=='archived':raise HTTPException(409,'Plano arquivado')
    activities=[dict(a) for a in p.actions]
    if data.index>=len(activities):raise HTTPException(422,'Atividade inexistente')
    old=activities[data.index]['done']
    activities[data.index].update(done=data.done,evidence=data.evidence.strip() if data.done else '')
    p.actions=activities
    p.progress=round(sum(bool(a['done']) for a in activities)*100/len(activities))
    p.status='completed' if p.progress==100 else 'active'
    log(db,user,'development_plan_updated','development_plan',p.id,before={'activity':data.index,'done':old},after={'activity':data.index,'done':data.done,'progress':p.progress})
    db.commit();return plan_json(p,e)

@router.post('/plans/{plan_id}/archive')
def archive_plan(plan_id:int,user:User=Depends(allowed('admin','recruiter')),db:Session=Depends(get_db)):
    p=scoped(db,DevelopmentPlan,user,plan_id);before=p.status;p.status='archived'
    log(db,user,'development_plan_archived','development_plan',p.id,before={'status':before},after={'status':'archived'})
    db.commit();return {'status':'archived'}

class LeaveIn(BaseModel):
    employee_id:int
    kind:Literal['vacation','personal','medical','other']='vacation'
    starts_on:str
    ends_on:str
    reason:str=Field(default='',max_length=2000)


def leave_json(x,e):
    return {'id':x.id,'employee_id':e.id,'employee':e.name,'department':e.department,'kind':x.kind,'starts_on':x.starts_on,'ends_on':x.ends_on,'days':x.days,'reason':x.reason,'status':x.status,'approver_id':x.approver_id,'decided_at':x.decided_at.isoformat() if x.decided_at else None}

@router.get('/leaves')
def leaves(status:str='',user:User=Depends(allowed(*ROLES)),db:Session=Depends(get_db)):
    people={e.id:e for e in db.scalars(select(Employee).where(Employee.company_id==user.company_id)).all() if user.role!='manager' or e.manager_id==user.id}
    stmt=select(LeaveRequest).where(LeaveRequest.company_id==user.company_id,LeaveRequest.employee_id.in_(list(people)))
    if status:stmt=stmt.where(LeaveRequest.status==status)
    return [leave_json(x,people[x.employee_id]) for x in db.scalars(stmt.order_by(LeaveRequest.created_at.desc())).all()]

@router.post('/leaves')
def request_leave(data:LeaveIn,user:User=Depends(allowed(*ROLES)),db:Session=Depends(get_db)):
    e=employee_scoped(db,user,data.employee_id)
    a,b=iso(data.starts_on),iso(data.ends_on)
    days=(b-a).days+1
    if days<=0 or days>366:raise HTTPException(422,'Período deve ser positivo e não pode exceder 366 dias')
    if e.status!='active':raise HTTPException(409,'Colaborador não está ativo')
    overlaps=db.scalar(select(LeaveRequest.id).where(LeaveRequest.company_id==user.company_id,LeaveRequest.employee_id==e.id,
        LeaveRequest.status.in_(['pending','approved']),LeaveRequest.starts_on<=data.ends_on,LeaveRequest.ends_on>=data.starts_on).limit(1))
    if overlaps:raise HTTPException(409,'Existe uma solicitação sobreposta para este colaborador')
    x=LeaveRequest(company_id=user.company_id,employee_id=e.id,kind=data.kind,starts_on=data.starts_on,ends_on=data.ends_on,days=days,reason=data.reason)
    db.add(x);db.flush();log(db,user,'leave_requested','leave_request',x.id,after={'employee_id':e.id,'period':[data.starts_on,data.ends_on]})
    db.commit();return leave_json(x,e)

class LeaveDecision(BaseModel):
    decision:Literal['approved','rejected']
    comment:str=Field(default='',max_length=500)

@router.post('/leaves/{leave_id}/decide')
def decide_leave(leave_id:int,data:LeaveDecision,user:User=Depends(allowed('admin','manager')),db:Session=Depends(get_db)):
    x=scoped(db,LeaveRequest,user,leave_id);e=employee_scoped(db,user,x.employee_id)
    if x.status!='pending':raise HTTPException(409,'Solicitação já decidida')
    x.status=data.decision;x.approver_id=user.id;x.decided_at=datetime.now(timezone.utc)
    log(db,user,'leave_decided','leave_request',x.id,before={'status':'pending'},after={'status':x.status,'comment':data.comment[:500]})
    db.commit();return leave_json(x,e)

@router.get('/insights')
def insights(user:User=Depends(allowed(*ROLES)),db:Session=Depends(get_db)):
    people=[e for e in db.scalars(select(Employee).where(Employee.company_id==user.company_id)).all() if user.role!='manager' or e.manager_id==user.id]
    ids={e.id for e in people};active=[e for e in people if e.status=='active']
    plans=[p for p in db.scalars(select(DevelopmentPlan).where(DevelopmentPlan.company_id==user.company_id)).all() if p.employee_id in ids]
    leaves=[l for l in db.scalars(select(LeaveRequest).where(LeaveRequest.company_id==user.company_id)).all() if l.employee_id in ids]
    dept=Counter(e.department for e in active)
    # Small-cohort suppression is intentionally enforced on the backend.
    return {'population':len(people),'active':len(active),'pending_leaves':sum(l.status=='pending' for l in leaves),
        'plan_count':len(plans),'completed_plans':sum(p.status=='completed' for p in plans),
        'development_completion':{'numerator':sum(p.status=='completed' for p in plans),'denominator':len(plans),'unit':'planos','interpretation':'Execução de PDI, não evidência de ganho de competência'},
        'departments':[{'name':name,'count':value if value>=5 else None,'suppressed':value<5} for name,value in sorted(dept.items())],
        'limits':['Populações menores que cinco não são mostradas por área','Dados descritivos não demonstram causalidade','Férias/afastamentos são registros, não cálculo de folha ou conformidade trabalhista']}
