"""Provision first administrator of an EMPTY tenant without hardcoded passwords.
Run on the production host with DATABASE_URL already set. No secret is printed.

Usage: python -m scripts.bootstrap_admin --company 'Acme' --slug acme --email admin@acme.com
"""
import argparse
import getpass
from sqlalchemy import select
from app.database import init_db,SessionLocal
from app.models import Company,User
from app.security import hash_password


def main():
    parser=argparse.ArgumentParser(description='Create first tenant and administrator')
    parser.add_argument('--company',required=True)
    parser.add_argument('--slug',required=True)
    parser.add_argument('--email',required=True)
    args=parser.parse_args()
    name=args.company.strip();slug=args.slug.lower().strip();email=args.email.lower().strip()
    if len(name)<2 or not slug.replace('-','').isalnum() or '@' not in email:
        parser.error('Nome, slug ou e-mail inválido')
    password=getpass.getpass('Senha (mínimo 12 caracteres): ')
    confirmation=getpass.getpass('Repetir senha: ')
    if password!=confirmation or len(password)<12:
        parser.error('A senha não confere ou tem menos de 12 caracteres')
    init_db()
    with SessionLocal() as db:
        if db.scalar(select(Company).where(Company.slug==slug)):
            parser.error('Empresa já existe; nenhuma alteração feita')
        if db.scalar(select(User).where(User.email==email)):
            parser.error('E-mail já cadastrado')
        company=Company(name=name,slug=slug)
        db.add(company);db.flush()
        db.add(User(company_id=company.id,email=email,name='Administrador inicial',role='admin',password_hash=hash_password(password),active=True))
        db.commit()
    print('Empresa e administrador criados. Configure MFA/SSO e políticas de sessão antes de produção.')

if __name__=='__main__':main()
