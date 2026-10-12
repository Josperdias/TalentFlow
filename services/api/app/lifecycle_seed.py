"""Fictitious, deterministic employee-lifecycle demo records; no sensitive data."""
from datetime import date,timedelta
from sqlalchemy import select,func
from .database import SessionLocal
from .models import Company,User,Employee,OnboardingItem,LearningCourse,LearningEnrollment,PerformanceGoal,PerformanceReview,CareerEvent

DEPARTMENTS=['Pessoas','Tecnologia','Operações','Produto','Financeiro','Relacionamento']
TITLES=['Analista de RH','Engenheiro de Software','Especialista em Processos','Product Designer','Analista Financeiro','Analista de Sucesso do Cliente']
FIRST=['Mariana','Bruno','Alice','André','Beatriz','Caio','Daniela','Eduardo','Fernanda','Gabriel','Isadora','Heitor','Júlia','Leonardo','Lívia','Matheus','Nina','Otávio','Paula','Ricardo','Sofia','Tiago','Vera','Yuri']
LAST=['Pereira','Dias','Costa','Almeida','Silva','Ferreira','Santos','Rodrigues']
COURSES=[('Proteção de dados e LGPD','Privacidade',3),('Integração cultural e processos','Integração',2),('Excel aplicado a indicadores','Análise de dados',6),('Liderança e feedback','Liderança',5),('Segurança da informação','Segurança',4),('Gestão de projetos ágeis','Gestão',7)]

def seed_lifecycle_if_empty():
    with SessionLocal() as db:
        comp=db.scalar(select(Company).where(Company.slug=='nexa'))
        if not comp or db.scalar(select(func.count()).select_from(Employee).where(Employee.company_id==comp.id)):return
        mgr=db.scalar(select(User).where(User.company_id==comp.id,User.role=='manager'))
        users=[];today=date.today()
        for i in range(24):
            hire=(today-timedelta(days=60+i*28)).isoformat()
            e=Employee(company_id=comp.id,employee_code=f'NX-COL-{i+1:04}',name=f'{FIRST[i]} {LAST[i%len(LAST)]}',work_email=f'colaborador{i+1:03}@example.test',department=DEPARTMENTS[i%6],job_title=TITLES[i%6],hire_date=hire,manager_id=mgr.id,status='exited' if i in (12,19) else 'active',exit_date=(today-timedelta(days=32 if i==12 else 80)).isoformat() if i in (12,19) else None,exit_kind='voluntary' if i==12 else 'involuntary' if i==19 else None)
            db.add(e);users.append(e)
        db.flush()
        catalog=[]
        for title,skill,hours in COURSES:
            c=LearningCourse(company_id=comp.id,title=title,skill=skill,duration_hours=hours);db.add(c);catalog.append(c)
        db.flush()
        for i,e in enumerate(users):
            for j,(phase,title,days) in enumerate([('Dia 1','Boas-vindas e apresentação',1),('Primeira semana','Configuração dos acessos',5),('Primeiro mês','Definição do PDI inicial',30),('Primeiros 90 dias','Conversa de 90 dias',90)]):
                db.add(OnboardingItem(company_id=comp.id,employee_id=e.id,title=title,phase=phase,due_date=(date.fromisoformat(e.hire_date)+timedelta(days=days)).isoformat(),completed_at=None if (i+j)%5==0 else __import__('datetime').datetime.now(__import__('datetime').timezone.utc)))
            for j in (i%6,(i+2)%6):
                db.add(LearningEnrollment(company_id=comp.id,employee_id=e.id,course_id=catalog[j].id,assigned_at=(today-timedelta(days=42)).isoformat(),completed_at=(today-timedelta(days=7)).isoformat() if (i+j)%3!=0 else None,status='completed' if (i+j)%3!=0 else 'assigned'))
            db.add(PerformanceGoal(company_id=comp.id,employee_id=e.id,title='Entregas mensais planejadas',metric_unit='entregas',target_value=10,actual_value=11 if i%4 else 6,due_date=(today+timedelta(days=30)).isoformat(),status='achieved' if i%4 else 'active'))
            if i%3==0:db.add(PerformanceReview(company_id=comp.id,employee_id=e.id,reviewer_id=mgr.id,period='2026-T3',criteria=[{'name':'Resultados','score':3+i%3,'weight':2},{'name':'Colaboração','score':4,'weight':1}],score=round((2*(3+i%3)+4)/3,2),feedback='Avaliação fictícia demonstrativa: requer calibração e contexto.'))
            if i%7==0:db.add(CareerEvent(company_id=comp.id,employee_id=e.id,kind='promotion',description='Progressão de carreira fictícia',effective_on=(today-timedelta(days=100)).isoformat()))
        db.commit()
