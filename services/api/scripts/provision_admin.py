"""Add a company and first administrator without putting passwords in source code.

Usage (within the project):
  APP_ENV=production DEMO_SEED=false DATABASE_URL=... python -m scripts.provision_admin --company 'ACME' --slug acme --email admin@acme.com
"""
from argparse import ArgumentParser
from getpass import getpass
from sqlalchemy import select
from app.database import SessionLocal, init_db
from app.models import Company, User
from app.security import hash_password

def run():
    args=ArgumentParser(description='Provision a real company and its first admin account')
    args.add_argument('--company',required=True)
    args.add_argument('--slug',required=True)
    args.add_argument('--email',required=True)
    args.add_argument('--user-name',default='Administrador')
    p=args.parse_args()
    password=getpass('Nova senha (>= 14 caracteres): ')
    if len(password)<14 or len(p.slug)>90 or '@' not in p.email:
        raise SystemExit('Dados inválidos ou senha muito curta')
    init_db()
    with SessionLocal() as db:
        company=db.scalar(select(Company).where(Company.slug==p.slug.lower().strip()))
        if not company:
            company=Company(name=p.company.strip(),slug=p.slug.lower().strip());db.add(company);db.flush()
        email=p.email.casefold().strip()
        if db.scalar(select(User).where(User.email==email,User.company_id==company.id)):
            raise SystemExit('Conta já cadastrada nesta empresa; operação cancelada')
        db.add(User(company_id=company.id,name=p.user_name,email=email,password_hash=hash_password(password),role='admin',active=True))
        db.commit()
        print('Administrador criado com sucesso na empresa',company.slug,'(ID:',company.id,')')
if __name__=='__main__':run()
