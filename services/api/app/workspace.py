"""Server-backed TalentFlow v1.1 workspace, tenant-scoped.

Phase 1 migration bridge: JSON snapshot of the legacy offline application.
Admin-only by design: granular, multi-role writes require normalized endpoints.
Never trust actor or company_id supplied in the snapshot.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import JSON, ForeignKey, Integer, String, DateTime, UniqueConstraint, select, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column
from .database import get_db
from .models import Base, User, AuditLog
from .security import allowed

router=APIRouter(prefix='/api/workspace',tags=['Connected Workspace'])
SEED_FILE=Path(__file__).resolve().parent.parent / 'private_demo_seed.json'
MAX_BYTES=2_000_000
JSON_FIELDS={
 'jobs','applications','candidates','employees','interviews','scorecards','communications','offers','audits',
 'onboarding_items','courses','enrollments','development_plans','goals','leave_requests',
 'competency_catalog','competency_roles','competency_evaluations','competencies',
 'assessment_definitions','assessment_responses','assessment_questions','assessments',
 'governance_actions','governance_decisions','governance_snapshots','governance_feedback',
 'people_cycles','people_reviews','people_calibrations','people_mobility_interests',
 'people_learning_evidence','people_leave_steps','people_kpi_snapshots'
}

class WorkspaceSnapshot(Base):
    __tablename__='workspace_snapshots'
    __table_args__=(UniqueConstraint('company_id',name='uq_workspace_company'),)
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    company_id:Mapped[int]=mapped_column(ForeignKey('companies.id'),nullable=False,index=True)
    data:Mapped[dict]=mapped_column(JSON().with_variant(JSONB(),'postgresql'),nullable=False)
    version:Mapped[int]=mapped_column(Integer,nullable=False,default=1)
    updated_by:Mapped[int]=mapped_column(ForeignKey('users.id'),nullable=False)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class WorkspaceWrite(BaseModel):
    version:int=Field(ge=0)
    data:dict[str,Any]


def validate_snapshot(data):
    try:
        raw=json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':'))
    except (TypeError,ValueError,OverflowError):
        raise HTTPException(422,'Estado inválido')
    if len(raw.encode('utf-8'))>MAX_BYTES:raise HTTPException(413,'Limite de 2 MB por estado excedido')
    if not isinstance(data.get('jobs'),list) or not isinstance(data.get('applications'),list):
        raise HTTPException(422,'Estrutura de vagas e candidaturas obrigatória')
    if any(k in data for k in ('__proto__','constructor','prototype')):
        raise HTTPException(422,'Chaves reservadas não permitidas')
    # Protect application from overlarge arrays and deeply nested payloads.
    for key,value in data.items():
        if isinstance(value,list) and len(value)>15_000:
            raise HTTPException(422,'Quantidade de registros acima do permitido')
    return raw


def seed_state():
    # Demo content must never be seeded in production.
    if os.getenv('APP_ENV','development').lower()=='production' or os.getenv('DEMO_SEED','false').lower()!='true':
        if SEED_FILE.exists():
            raw=json.loads(SEED_FILE.read_text(encoding='utf-8'))
            return {k:[] if isinstance(v,list) else ({} if isinstance(v,dict) else None) for k,v in raw.items()}
        return {'jobs':[],'applications':[],'candidates':[],'employees':[],'audit':[]}
    return json.loads(SEED_FILE.read_text(encoding='utf-8'))


def get_or_create(db:Session,user:User):
    entry=db.scalar(select(WorkspaceSnapshot).where(WorkspaceSnapshot.company_id==user.company_id))
    if entry:return entry
    entry=WorkspaceSnapshot(company_id=user.company_id,data=seed_state(),version=1,updated_by=user.id)
    db.add(entry)
    try:
        db.commit()
    except Exception:
        db.rollback()
        entry=db.scalar(select(WorkspaceSnapshot).where(WorkspaceSnapshot.company_id==user.company_id))
        if not entry:raise
    return entry


@router.get('/state')
def get_workspace(user:User=Depends(allowed('admin')),db:Session=Depends(get_db)):
    row=get_or_create(db,user)
    return {'version':row.version,'state':row.data,'updated_at':row.updated_at.isoformat(),'mode':'connected','role':user.role}


@router.post('/state')
def update_workspace(payload:WorkspaceWrite,request:Request,user:User=Depends(allowed('admin')),db:Session=Depends(get_db)):
    validate_snapshot(payload.data)
    # SELECT FOR UPDATE provides a serial write lock in PostgreSQL.
    row=db.scalar(select(WorkspaceSnapshot).where(WorkspaceSnapshot.company_id==user.company_id).with_for_update())
    if row is None:
        row=get_or_create(db,user)
    if payload.version!=row.version:
        raise HTTPException(status_code=409,detail={'message':'Estado modificado em outra sessão. Atualize para revisar antes de editar novamente.','current_version':row.version})
    old=row.data
    changed=[]
    for k in set(old)|set(payload.data):
        if old.get(k)!=payload.data.get(k): changed.append(k)
    if not changed:return {'version':row.version,'updated_at':row.updated_at.isoformat(),'changed':[]}
    before_counts={k:len(old.get(k,[])) for k in changed if isinstance(old.get(k),list)}
    after_counts={k:len(payload.data.get(k,[])) for k in changed if isinstance(payload.data.get(k),list)}
    changed_at=datetime.now(timezone.utc)
    result=db.execute(update(WorkspaceSnapshot).where(
        WorkspaceSnapshot.id==row.id,
        WorkspaceSnapshot.company_id==user.company_id,
        WorkspaceSnapshot.version==payload.version
    ).values(data=payload.data,version=payload.version+1,updated_by=user.id,updated_at=changed_at))
    if result.rowcount!=1:
        db.rollback()
        raise HTTPException(409,'Versão alterada por outra sessão; atualize antes de salvar')
    db.add(AuditLog(company_id=user.company_id,user_id=user.id,action='workspace_changed',entity='workspace',entity_id=row.id,before_json={'counts':before_counts,'version':payload.version},after_json={'collections':sorted(changed),'counts':after_counts,'version':payload.version+1}))
    db.commit()
    return {'version':payload.version+1,'updated_at':changed_at.isoformat(),'changed':sorted(changed)}

@router.get('/status')
def workspace_status(user:User=Depends(allowed('admin')),db:Session=Depends(get_db)):
    row=db.scalar(select(WorkspaceSnapshot).where(WorkspaceSnapshot.company_id==user.company_id))
    return {'connected':True,'company_id':user.company_id,'version':row.version if row else 0,'updated_at':row.updated_at.isoformat() if row else None,'role':user.role}


@router.get('/metrics')
def workspace_metrics(user:User=Depends(allowed('admin')),db:Session=Depends(get_db)):
    data=get_or_create(db,user).data
    def coll(name):
        value=data.get(name,[])
        return value if isinstance(value,list) else []
    apps=coll('applications');plans=coll('development_plans')
    hired=sum(1 for a in apps if a.get('status')=='hired')
    finished=sum(1 for p in plans if p.get('status')=='completed')
    def indicator(number,denominator):
        return {'numerator':number,'denominator':denominator,'percentage':round(number*100/denominator,1) if denominator else None}
    return {'source':'workspace_snapshot','data_kind':'demo' if os.getenv('DEMO_SEED','false').lower()=='true' else 'user_entered',
      'counts':{'jobs':len(coll('jobs')),'candidates':len(coll('candidates')),'applications':len(apps),
                'employees':len(coll('employees')),'interviews':len(coll('interviews'))},
      'indicators':{'hired_applications':indicator(hired,len(apps)),
                    'completed_development_plans':indicator(finished,len(plans))},
      'methodology':'Apenas registros do estado da empresa autenticada. Indicadores descritivos, não estimativas de efetividade.'}
