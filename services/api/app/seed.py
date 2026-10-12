"""Deterministic synthetic tenant fixtures (never real candidate data)."""
import random,os
from datetime import datetime,timedelta,timezone
from sqlalchemy import select,func
from .database import SessionLocal
from .models import *
from .security import hash_password
NAMES=['Ana','Bruno','Camila','Daniel','Elisa','Felipe','Gabriela','Henrique','Isabela','João','Karina','Lucas','Marina','Nicolas','Olívia','Pedro','Renata','Samuel','Tatiana','Vinícius','Yasmin','Caio','Beatriz','André','Luíza','Rafael','Carolina','Thiago','Letícia','Victor']
SURNAMES=['Silva','Pereira','Santos','Costa','Oliveira','Dias','Almeida','Ferreira','Souza','Rodrigues','Lima','Carvalho','Nascimento','Barbosa','Ribeiro']
JOBS=[('Product Designer','Produto'),('Analista de RH','Pessoas'),('Desenvolvedor Front-end','Tecnologia'),('Engenheiro de Dados','Tecnologia'),('Analista Financeiro','Financeiro'),('Tech Recruiter','Pessoas'),('Customer Success','Relacionamento'),('Coordenador de Operações','Operações'),('Analista de Marketing','Marketing'),('UX Researcher','Produto')]
STAGES=['Novos','Triagem','Entrevista RH','Entrevista Gestor','Teste','Finalistas','Proposta','Contratado','Reprovado']
SKILLS=['Excel','Recrutamento','Python','React','SQL','Power BI','Comunicação','Figma','Liderança','Análise de dados','Gestão de projetos']

def seed_if_empty():
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Company))>0:return
        rng=random.Random(44)
        nex=Company(name='Nexa Tecnologia',slug='nexa',description='Tecnologia feita por pessoas. Construímos produtos digitais e times que transformam negócios.')
        db.add(nex);db.flush()
        users=[]
        for name,email,role in [('Marina Almeida','admin@nexa.demo','admin'),('Luiza Costa','recrutador@nexa.demo','recruiter'),('Rafael Dias','gestor@nexa.demo','manager'),('Carolina Lima','entrevistador@nexa.demo','interviewer'),('Pessoa Candidata','candidato@nexa.demo','candidate')]:
            u=User(company_id=nex.id,name=name,email=email,password_hash=hash_password('Demo@2026!'),role=role)
            db.add(u);users.append(u)
        db.flush()
        other=Company(name='Orbe Soluções',slug='orbe',description='Tenant independente para testes de isolamento')
        db.add(other);db.flush()
        db.add(User(company_id=other.id,name='Admin Orbe',email='admin@orbe.demo',password_hash=hash_password('Demo@2026!'),role='admin'))
        db.flush()
        jobs=[];stages_by_job={}
        for i,(title,department) in enumerate(JOBS):
            status='open' if i<7 else ('approval' if i==7 else 'closed')
            j=Job(company_id=nex.id,code=f'NX-{1001+i}',title=title,department=department,location=['Brasília, DF','São Paulo, SP','Remoto — Brasil'][i%3],modality=['Híbrido','Remoto','Presencial'][i%3],seniority=['Júnior','Pleno','Sênior'][i%3],employment='CLT',salary_min=3000+i*380,salary_max=5200+i*560,description=f'Buscamos uma pessoa para atuar como {title}, colaborando com equipes multidisciplinares e entregando soluções relevantes.',requirements='Comunicação, resolução de problemas e domínio das ferramentas da área.',benefits='Plano de saúde, auxílio alimentação, desenvolvimento profissional.',positions=1+(i%2),status=status,due_date=(datetime.now()+timedelta(days=20+i*4)).strftime('%Y-%m-%d'),manager_id=users[2].id,recruiter_id=users[1].id,created_at=now()-timedelta(days=75-i*4))
            db.add(j);db.flush();jobs.append(j)
            sts=[]
            for pos,label in enumerate(STAGES):
                s=JobStage(company_id=nex.id,job_id=j.id,name=label,order=pos,kind='hired' if pos==7 else 'rejected' if pos==8 else 'active');db.add(s);db.flush();sts.append(s)
            stages_by_job[j.id]=sts
        people=[]
        for i in range(120):
            name=f'{NAMES[i%len(NAMES)]} {SURNAMES[(i*7+i//len(NAMES))%len(SURNAMES)]}'
            abilities=rng.sample(SKILLS,4)
            c=Candidate(company_id=nex.id,name=name,email='candidato@nexa.demo' if i==0 else f'talento{i+1:03}@example.test',phone=f'(61) 9{rng.randint(1000,9999)}-{rng.randint(1000,9999)}',location=['Brasília, DF','São Paulo, SP','Goiânia, GO','Belo Horizonte, MG'][i%4],title=JOBS[i%len(JOBS)][0],source=['LinkedIn','Página de carreiras','Indicação','Banco de talentos','Indeed'][i%5],skills=', '.join(abilities),experience_years=i%12,education=['Ensino Superior Completo','Pós-graduação','Superior em andamento'][i%3],resume_text=f'{name}\n{JOBS[i%10][0]}\n{rng.randint(1,10)} anos de experiência. Competências: {", ".join(abilities)}. Formação superior e projetos de impacto.',consent=True,created_at=now()-timedelta(days=rng.randint(1,105)))
            db.add(c);people.append(c)
        db.flush()
        apps=[]
        for i,c in enumerate(people):
            for k in range(1 if i>35 else 2):
                j=jobs[(i+k*3)%len(jobs)]
                sts=stages_by_job[j.id]
                stage=sts[7] if i%29==0 else sts[8] if i%23==0 else sts[1+(i+k)%6] if i%4 else sts[0]
                app=Application(company_id=nex.id,candidate_id=c.id,job_id=j.id,stage_id=stage.id,status='hired' if stage.kind=='hired' else 'rejected' if stage.kind=='rejected' else 'active',fit=45+(i*11+k*13)%55,fit_reason='Classificação demonstrativa; requer revisão humana',created_at=now()-timedelta(days=rng.randint(1,75)),last_activity_at=now()-timedelta(days=rng.randint(0,16)))
                db.add(app);apps.append(app)
        db.flush()
        for idx,app in enumerate(apps):
            if idx%4==0:
                db.add(Interview(company_id=nex.id,application_id=app.id,interviewer_id=users[3].id,starts_at=(datetime.now()+timedelta(days=1+idx%22,hours=idx%8)).strftime('%Y-%m-%dT%H:%M'),duration_minutes=45,status='scheduled' if idx%3 else 'confirmed'))
            if idx%3==0:
                criteria=[{'name':'Comunicação','weight':1,'score':3+idx%3},{'name':'Conhecimento técnico','weight':2,'score':2+idx%4},{'name':'Colaboração','weight':1,'score':4}]
                value=round(sum(x['weight']*x['score'] for x in criteria)/4,2)
                db.add(Scorecard(company_id=nex.id,application_id=app.id,author_id=users[3].id,criteria=criteria,result=value,notes='Avaliação estruturada fictícia para demonstração.'))
            if idx%5==0:
                db.add(Communication(company_id=nex.id,application_id=app.id,channel='email',subject='Atualização sobre sua candidatura',body='Olá! Obrigado por participar do nosso processo seletivo.',status='queued_mock'))
            if idx%7==0:
                db.add(Activity(company_id=nex.id,application_id=app.id,author_id=users[1].id,kind='note',description='Perfil revisado durante triagem.'))
        db.add(Automation(company_id=nex.id,title='Convite para entrevista de RH',trigger='stage_changed',condition_json={'stage':'Entrevista RH'},action_json={'type':'email','template':'Convite para entrevista'},enabled=True))
        db.add(Automation(company_id=nex.id,title='Comunicação de reprovação',trigger='stage_changed',condition_json={'stage':'Reprovado'},action_json={'type':'email','template':'Devolutiva do processo'},enabled=True))
        db.add(TestDefinition(company_id=nex.id,title='Conhecimentos digitais',duration_minutes=25,pass_percent=70,questions=[{'text':'Qual fórmula soma valores no Excel?','type':'multiple_choice','options':['=SOMA()','=TOTAL()','=JUNTAR()'],'correct':0,'points':5},{'text':'Descreva um projeto de melhoria de processos','type':'essay','points':5}]))
        db.add(TalentList(company_id=nex.id,name='Profissionais em destaque',candidate_ids=[p.id for p in people[:12]]))
        for i in range(15): db.add(Task(company_id=nex.id,title=['Revisar currículo','Enviar parecer','Confirmar entrevista'][i%3],application_id=apps[i].id,assignee_id=users[1].id,due_date=(datetime.now()+timedelta(days=i%6)).strftime('%Y-%m-%d'),completed=i%4==0))
        db.commit()
