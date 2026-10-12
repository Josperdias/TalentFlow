"""Deterministic fictional workforce demonstration records (dev only)."""
from datetime import date,timedelta
from sqlalchemy import select
from .database import SessionLocal
from .models import Employee,DevelopmentPlan,LeaveRequest,User


def seed_workforce_if_empty():
    with SessionLocal() as db:
        if db.scalar(select(DevelopmentPlan.id).where(DevelopmentPlan.company_id==1).limit(1)):
            return
        people=db.scalars(select(Employee).where(Employee.company_id==1,Employee.status=='active').order_by(Employee.id)).all()
        admin=db.scalar(select(User).where(User.company_id==1,User.role=='admin'))
        if not people or not admin:return
        labels=[('Comunicação consultiva','Comunicação','Realizar conversas de alinhamento documentadas'),('Análise de dados','Excel / BI','Construir um relatório com métricas verificadas'),('Liderança colaborativa','Liderança','Conduzir reuniões de acompanhamento estruturadas'),('Qualidade de processos','Gestão','Revisar um procedimento com evidências'),('Segurança da informação','Privacidade','Aplicar classificação e minimização de dados'),('Aprendizagem contínua','Pesquisa','Documentar um aprendizado aplicado ao trabalho'),('Planejamento','Organização','Definir metas trimestrais observáveis'),('Atendimento empático','Relacionamento','Melhorar padrões de comunicação da equipe')]
        today=date.today()
        for idx,e in enumerate(people[:8]):
            title,skill,goal=labels[idx]
            actions=[{'title':label,'done':done,'evidence':'Registro de execução no ambiente fictício' if done else ''} for label,done in zip(['Estudar referência do tema','Aplicar exercício prático','Apresentar aprendizado à equipe'],[True,idx%2==0,idx%3==0])]
            progress=round(sum(x['done'] for x in actions)/len(actions)*100)
            db.add(DevelopmentPlan(company_id=1,employee_id=e.id,title=title,competency=skill,goal=goal,actions=actions,progress=progress,status='completed' if progress==100 else 'active',due_date=(today+timedelta(days=30+idx*13)).isoformat(),owner_id=admin.id))
        for idx,e in enumerate(people[:6]):
            start=today+timedelta(days=23+idx*18)
            db.add(LeaveRequest(company_id=1,employee_id=e.id,kind=['vacation','personal','vacation','other','vacation','personal'][idx],starts_on=start.isoformat(),ends_on=(start+timedelta(days=3+idx)).isoformat(),days=4+idx,reason='Solicitação fictícia de demonstração',status=['pending','approved','pending','rejected','approved','pending'][idx],approver_id=admin.id if idx in (1,3,4) else None))
        db.commit()
