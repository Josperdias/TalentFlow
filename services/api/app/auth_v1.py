"""Autenticação da API v1 para os três clientes.

* Site (mesma origem, via proxy /api): cookie HttpOnly + token CSRF  -> POST /auth/login
* Apps nativos (Android/Windows):   access token curto (15 min) + refresh token opaco
  com rotação e detecção de reuso                                   -> POST /auth/token, /auth/refresh

Somente hashes SHA-256 de tokens são persistidos. Limites de tentativa usam o mesmo
rate limiter do restante da API.  Fluxo OAuth 2.0 Authorization Code + PKCE com navegador
do sistema NÃO está implementado nesta versão (ver docs/STATUS.md).
"""
import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .database import get_db
from .hardening import csrf_value, rate_limit, reset_rate_limit
from .models import AuditLog, Company, RefreshToken, Session as LoginSession, User
from .security import bearer_token, create_session, current_user, verify_password

router = APIRouter(prefix='/api/v1', tags=['Auth'])

ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=30)
CLIENTS = ('web', 'android', 'windows', 'cli')
API_VERSION = '1.0.0'


def _h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def user_payload(u: User, db: Session) -> dict:
    company = db.get(Company, u.company_id)
    return dict(id=u.id, name=u.name, email=u.email, role=u.role, company_id=u.company_id,
                company=company.name if company else '')


def _audit(db: Session, user: User, action: str, after: dict | None = None) -> None:
    db.add(AuditLog(company_id=user.company_id, user_id=user.id, action=action, entity='user',
                    entity_id=user.id, after_json=after or {}))


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)


class TokenIn(LoginIn):
    client: str = Field(default='cli', max_length=20)
    device: str = Field(default='', max_length=120)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)


def _authenticate(db: Session, request: Request, data: LoginIn) -> User:
    email = data.email.lower().strip()
    rate_limit(db, 'login-ip', request.client.host if request.client else 'unknown', int(os.getenv('TF_LOGIN_IP_LIMIT', '40')))
    rate_limit(db, 'login-account', email, 8)
    user = db.scalar(select(User).where(User.email == email, User.active.is_(True)))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, 'Credenciais inválidas')
    reset_rate_limit(db, 'login-account', email)
    return user


def _issue_pair(db: Session, user: User, client: str, device: str, family: str) -> dict:
    access = secrets.token_urlsafe(40)
    refresh = secrets.token_urlsafe(48)
    now = _now()
    db.add(LoginSession(id=_h(access), user_id=user.id, kind='access', client=client,
                        family_id=family, expires_at=now + ACCESS_TTL))
    db.add(RefreshToken(user_id=user.id, family_id=family, token_hash=_h(refresh), client=client,
                        device=device[:120], expires_at=now + REFRESH_TTL))
    return {'token_type': 'Bearer', 'access_token': access, 'expires_in': int(ACCESS_TTL.total_seconds()),
            'refresh_token': refresh, 'refresh_expires_in': int(REFRESH_TTL.total_seconds())}


def _revoke_family(db: Session, family: str) -> None:
    db.execute(update(RefreshToken).where(RefreshToken.family_id == family, RefreshToken.revoked_at.is_(None))
               .values(revoked_at=_now()))
    for s in db.scalars(select(LoginSession).where(LoginSession.family_id == family)).all():
        db.delete(s)


# ---- Site (cookie + CSRF) -------------------------------------------------------------
@router.post('/auth/login', summary='Login do site (cookie HttpOnly)')
def login(data: LoginIn, response: Response, request: Request, db: Session = Depends(get_db)):
    user = _authenticate(db, request, data)
    token = create_session(db, user)
    response.set_cookie('tf_session', token, httponly=True,
                        secure=os.getenv('COOKIE_SECURE', 'false').lower() == 'true',
                        samesite='lax', path='/', max_age=43200)
    _audit(db, user, 'login', {'client': 'web'})
    db.commit()
    return {'user': user_payload(user, db), 'csrf': csrf_value(token)}


@router.get('/auth/csrf')
def csrf(request: Request, user: User = Depends(current_user)):
    cookie = request.cookies.get('tf_session')
    if not cookie:
        raise HTTPException(400, 'Token CSRF só se aplica a sessões de navegador')
    return {'token': csrf_value(cookie)}


# ---- Apps nativos (Bearer) --------------------------------------------------------------
@router.post('/auth/token', summary='Login de cliente nativo: access + refresh token')
def token(data: TokenIn, request: Request, db: Session = Depends(get_db)):
    if data.client not in CLIENTS:
        raise HTTPException(422, 'Cliente desconhecido')
    user = _authenticate(db, request, data)
    pair = _issue_pair(db, user, data.client, data.device, str(uuid.uuid4()))
    _audit(db, user, 'login', {'client': data.client, 'device': data.device[:120]})
    db.commit()
    return {**pair, 'user': user_payload(user, db)}


@router.post('/auth/refresh', summary='Rotaciona o refresh token (uso único)')
def refresh(data: RefreshIn, request: Request, db: Session = Depends(get_db)):
    rate_limit(db, 'refresh-ip', request.client.host if request.client else 'unknown', 120)
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == _h(data.refresh_token)).with_for_update())
    if not row:
        raise HTTPException(401, 'Refresh token inválido')
    user = db.get(User, row.user_id)
    if row.revoked_at is not None or _aware(row.expires_at) < _now() or not user or not user.active:
        raise HTTPException(401, 'Refresh token expirado ou revogado')
    if row.used_at is not None:
        # Reapresentação de um token já consumido: possível roubo -> derruba a família inteira.
        _revoke_family(db, row.family_id)
        _audit(db, user, 'refresh_reuse_detected', {'family': row.family_id, 'client': row.client})
        db.commit()
        raise HTTPException(401, 'Refresh token reutilizado; sessão encerrada por segurança')
    row.used_at = _now()
    pair = _issue_pair(db, user, row.client, row.device, row.family_id)
    db.commit()
    return {**pair, 'user': user_payload(user, db)}


# ---- Comuns ---------------------------------------------------------------------------------
def _current_session(request: Request, db: Session) -> LoginSession | None:
    raw = bearer_token(request) or request.cookies.get('tf_session', '')
    return db.get(LoginSession, _h(raw)) if raw else None


@router.post('/auth/logout')
def logout(request: Request, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    session = _current_session(request, db)
    if session is not None:
        if session.family_id:
            _revoke_family(db, session.family_id)
        else:
            db.delete(session)
    _audit(db, user, 'logout')
    db.commit()
    response.delete_cookie('tf_session')
    return {'ok': True}


@router.get('/auth/sessions')
def sessions(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    current = _current_session(request, db)
    rows = db.scalars(select(LoginSession).where(LoginSession.user_id == user.id,
                                                 LoginSession.expires_at > _now())).all()
    # Uma entrada por família de refresh (dispositivo) ou por cookie.
    seen, out = set(), []
    for s in rows:
        key = s.family_id or s.id
        if key in seen:
            continue
        seen.add(key)
        out.append({'id': key[:12], 'client': s.client, 'kind': s.kind,
                    'expires_at': _aware(s.expires_at).isoformat(),
                    'current': bool(current and (current.family_id or current.id) == key)})
    return out


@router.post('/auth/sessions/revoke-others')
def revoke_others(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    current = _current_session(request, db)
    keep = (current.family_id or current.id) if current else None
    revoked = 0
    for s in db.scalars(select(LoginSession).where(LoginSession.user_id == user.id)).all():
        key = s.family_id or s.id
        if key == keep:
            continue
        if s.family_id:
            _revoke_family(db, s.family_id)
        else:
            db.delete(s)
        revoked += 1
    _audit(db, user, 'other_sessions_revoked', {'count': revoked})
    db.commit()
    return {'revoked': revoked}


@router.get('/me')
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {'user': user_payload(user, db)}


@router.get('/health', summary='Estado da API e versões mínimas de cliente')
def health():
    return {'status': 'ok', 'product': 'TalentFlow People', 'api_version': API_VERSION,
            # Clientes abaixo destas versões devem avisar o usuário e oferecer atualização.
            'min_client_version': {'web': '1.0.0', 'android': '1.0.0', 'windows': '1.0.0'}}
