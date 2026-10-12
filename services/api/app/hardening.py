"""Shared defensive controls. Guidelines: OWASP CSRF and Authentication Cheat Sheets.

The rate limiter uses the database so attempts are tracked across worker processes;
production installations should put equivalent limits at their edge proxy too.
"""
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from fastapi import HTTPException, Request
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from .models import RateLimitEvent

MUTATING={'POST','PUT','PATCH','DELETE'}

def csrf_value(session_token: str) -> str:
    """Bound to a random HttpOnly session cookie, returned only to same-origin clients."""
    return hashlib.sha256((session_token+'|tf-csrf-v1').encode()).hexdigest()

def validate_browser_request(request: Request):
    if request.method not in MUTATING or not request.url.path.startswith('/api/'):
        return
    site=request.headers.get('sec-fetch-site','').lower()
    if site in ('cross-site','same-site'):
        raise HTTPException(403,'Requisição de outra origem bloqueada')
    trusted=f'{request.url.scheme}://{request.url.netloc}'
    for key in ('origin','referer'):
        source=request.headers.get(key)
        if source:
            try:
                part=urlsplit(source)
                if f'{part.scheme}://{part.netloc}' != trusted:
                    raise HTTPException(403,'Origem inválida')
            except ValueError:
                raise HTTPException(403,'Origem inválida')
            break
    token=request.cookies.get('tf_session')
    if token and request.url.path!='/api/auth/login':
        received=request.headers.get('x-tf-csrf','')
        if not hmac.compare_digest(received,csrf_value(token)):
            raise HTTPException(403,'Token de proteção de sessão ausente ou inválido')


def rate_limit(db:Session,bucket:str,identifier:str,limit:int,minutes:int=15):
    """Record each attempt (including successful public submissions); fail closed at cap."""
    if not identifier: identifier='unknown'
    key=hashlib.sha256((bucket+':'+identifier.casefold()).encode()).hexdigest()
    now=datetime.now(timezone.utc)
    cutoff=(now-timedelta(minutes=minutes)).replace(tzinfo=None)
    count=db.scalar(select(func.count()).select_from(RateLimitEvent).where(
        RateLimitEvent.bucket_key==key,RateLimitEvent.created_at>=cutoff)) or 0
    if count>=limit:
        raise HTTPException(status_code=429,detail='Muitas tentativas. Aguarde e tente novamente.',headers={'Retry-After':str(minutes*60)})
    db.add(RateLimitEvent(bucket_key=key))
    # Opportunistic cleanup; keeps the table bounded without a cron requirement.
    if count==0:
        db.execute(delete(RateLimitEvent).where(RateLimitEvent.created_at < (now-timedelta(days=2)).replace(tzinfo=None)))
    db.commit()

def reset_rate_limit(db:Session,bucket:str,identifier:str):
    key=hashlib.sha256((bucket+':'+identifier.casefold()).encode()).hexdigest()
    db.execute(delete(RateLimitEvent).where(RateLimitEvent.bucket_key==key))
    db.commit()
