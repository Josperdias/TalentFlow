import hashlib,hmac,os,secrets
from datetime import datetime,timezone,timedelta
from fastapi import Depends,HTTPException,Request
from sqlalchemy.orm import Session
from .database import get_db
from .models import User,Session as LoginSession

def hash_password(password:str)->str:
    salt=os.urandom(16); key=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,240000)
    return salt.hex()+':'+key.hex()
def verify_password(password:str,stored:str)->bool:
    try:
        salt,key=stored.split(':');calc=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),240000)
        return hmac.compare_digest(calc,bytes.fromhex(key))
    except (ValueError,TypeError):return False

def create_session(db:Session,user:User):
    token=secrets.token_urlsafe(40); digest=hashlib.sha256(token.encode()).hexdigest()
    db.add(LoginSession(id=digest,user_id=user.id,expires_at=datetime.now(timezone.utc)+timedelta(hours=12)));db.commit()
    return token

def current_user(request:Request,db:Session=Depends(get_db)):
    token=request.cookies.get('tf_session')
    if not token:raise HTTPException(401,'Faça login para continuar')
    session=db.get(LoginSession,hashlib.sha256(token.encode()).hexdigest())
    if not session or session.expires_at.replace(tzinfo=timezone.utc)<datetime.now(timezone.utc):
        raise HTTPException(401,'Sessão expirada')
    user=db.get(User,session.user_id)
    if not user or not user.active:raise HTTPException(401,'Usuário inativo')
    return user

def allowed(*roles):
    def dependency(user:User=Depends(current_user)):
        if user.role not in roles:raise HTTPException(403,'Sem permissão para executar esta ação')
        return user
    return dependency
