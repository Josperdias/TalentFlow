"""Sincronização entre clientes: feed incremental de mudanças por empresa.

Fonte: tabela audit_logs (id crescente, escrita na mesma transação da mutação).
O feed serve como *dica de invalidação*: o cliente descobre que algo mudou e rebusca
a lista pelos endpoints normais, que aplicam RBAC. Por isso o feed não carrega
before/after e só expõe entity_id a papéis que já enxergam a empresa inteira.
Sem simulação offline: se não houver conexão, o cliente exibe o estado de desconexão.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import get_db
from .models import AuditLog, User
from .security import current_user

router = APIRouter(prefix='/api/v1', tags=['Sync'])
FULL_VISIBILITY = ('admin', 'recruiter')


@router.get('/changes', summary='Mudanças da empresa após um cursor')
def changes(after: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500),
            user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLog).where(AuditLog.company_id == user.company_id, AuditLog.id > after)
                      .order_by(AuditLog.id).limit(limit)).all()
    detailed = user.role in FULL_VISIBILITY
    items = [{'seq': r.id, 'entity': r.entity, 'action': r.action,
              'entity_id': r.entity_id if detailed else None,
              'actor_id': r.user_id if detailed else None,
              'at': r.created_at.isoformat()} for r in rows]
    latest = db.scalar(select(func.max(AuditLog.id)).where(AuditLog.company_id == user.company_id)) or 0
    return {'cursor': items[-1]['seq'] if items else max(after, 0), 'latest': latest,
            'has_more': bool(items) and items[-1]['seq'] < latest,
            'entities': sorted({i['entity'] for i in items}), 'items': items}


@router.get('/changes/cursor', summary='Cursor atual (para iniciar a sincronização sem histórico)')
def cursor(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {'cursor': db.scalar(select(func.max(AuditLog.id)).where(AuditLog.company_id == user.company_id)) or 0}
