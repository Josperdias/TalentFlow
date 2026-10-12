"""Tenant-isolated TalentFlow data model. PostgreSQL-ready SQLAlchemy mappings."""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Float, Text, UniqueConstraint, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

def now(): return datetime.now(timezone.utc)

class Base(DeclarativeBase): pass

class TenantMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('companies.id'), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Company(Base):
    __tablename__ = 'companies'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text, default='')

class User(TenantMixin, Base):
    __tablename__ = 'users'
    __table_args__ = (UniqueConstraint('company_id','email'),)
    email: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(24), default='recruiter')
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Session(Base):
    __tablename__ = 'sessions'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class Job(TenantMixin, Base):
    __tablename__ = 'jobs'
    __table_args__ = (UniqueConstraint('company_id','code'),)
    code: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200))
    department: Mapped[str] = mapped_column(String(100), default='Tecnologia')
    location: Mapped[str] = mapped_column(String(100), default='Brasília, DF')
    modality: Mapped[str] = mapped_column(String(30), default='Híbrido')
    seniority: Mapped[str] = mapped_column(String(30), default='Pleno')
    employment: Mapped[str] = mapped_column(String(30), default='CLT')
    salary_min: Mapped[int] = mapped_column(Integer, default=0)
    salary_max: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default='')
    requirements: Mapped[str] = mapped_column(Text, default='')
    benefits: Mapped[str] = mapped_column(Text, default='')
    positions: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(28), default='open')
    due_date: Mapped[str] = mapped_column(String(12), default='')
    manager_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    recruiter_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)

class JobStage(TenantMixin, Base):
    __tablename__='job_stages'
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id'), index=True)
    name: Mapped[str] = mapped_column(String(80))
    order: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(20), default='active')

class Candidate(TenantMixin, Base):
    __tablename__='candidates'
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(60), default='')
    location: Mapped[str] = mapped_column(String(120), default='')
    title: Mapped[str] = mapped_column(String(130), default='')
    source: Mapped[str] = mapped_column(String(70), default='LinkedIn')
    skills: Mapped[str] = mapped_column(Text, default='')
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    education: Mapped[str] = mapped_column(String(150), default='')
    resume_text: Mapped[str] = mapped_column(Text, default='')
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)

class Application(TenantMixin, Base):
    __tablename__='applications'
    __table_args__=(UniqueConstraint('company_id','job_id','candidate_id'),)
    candidate_id: Mapped[int] = mapped_column(ForeignKey('candidates.id'), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id'), index=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey('job_stages.id'))
    status: Mapped[str] = mapped_column(String(20), default='active')
    fit: Mapped[int] = mapped_column(Integer, default=50)
    fit_reason: Mapped[str] = mapped_column(Text, default='Não avaliado')
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Interview(TenantMixin, Base):
    __tablename__='interviews'
    application_id: Mapped[int] = mapped_column(ForeignKey('applications.id'), index=True)
    interviewer_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    starts_at: Mapped[str] = mapped_column(String(40))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=45)
    meeting_link: Mapped[str] = mapped_column(String(300), default='')
    status: Mapped[str] = mapped_column(String(24), default='scheduled')
    notes: Mapped[str] = mapped_column(Text, default='')

class Scorecard(TenantMixin, Base):
    __tablename__='scorecards'
    application_id: Mapped[int] = mapped_column(ForeignKey('applications.id'), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    criteria: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, default='')
    result: Mapped[float] = mapped_column(Float, default=0.0)

class Activity(TenantMixin, Base):
    __tablename__='activities'
    application_id: Mapped[int | None] = mapped_column(ForeignKey('applications.id'), nullable=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    kind: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

class Communication(TenantMixin, Base):
    __tablename__='communications'
    application_id: Mapped[int] = mapped_column(ForeignKey('applications.id'), index=True)
    channel: Mapped[str] = mapped_column(String(25), default='email')
    subject: Mapped[str] = mapped_column(String(200), default='')
    body: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(30), default='queued_mock')

class Offer(TenantMixin, Base):
    __tablename__='offers'
    application_id: Mapped[int] = mapped_column(ForeignKey('applications.id'), index=True)
    salary: Mapped[int] = mapped_column(Integer)
    benefits: Mapped[str] = mapped_column(Text, default='')
    start_date: Mapped[str] = mapped_column(String(12), default='')
    expires_on: Mapped[str] = mapped_column(String(12), default='')
    status: Mapped[str] = mapped_column(String(30), default='draft')
    token: Mapped[str] = mapped_column(String(80), unique=True)
    notes: Mapped[str] = mapped_column(Text, default='')

class Automation(TenantMixin, Base):
    __tablename__='automations'
    title: Mapped[str] = mapped_column(String(120))
    trigger: Mapped[str] = mapped_column(String(80))
    condition_json: Mapped[dict] = mapped_column(JSON, default=dict)
    action_json: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    runs: Mapped[int] = mapped_column(Integer, default=0)

class AutomationRun(TenantMixin, Base):
    __tablename__='automation_runs'
    automation_id: Mapped[int] = mapped_column(ForeignKey('automations.id'))
    application_id: Mapped[int | None] = mapped_column(ForeignKey('applications.id'), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='success')
    detail: Mapped[str] = mapped_column(Text, default='')

class AuditLog(TenantMixin, Base):
    __tablename__='audit_logs'
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    action: Mapped[str] = mapped_column(String(60))
    entity: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[int] = mapped_column(Integer)
    before_json: Mapped[dict] = mapped_column(JSON, default=dict)
    after_json: Mapped[dict] = mapped_column(JSON, default=dict)

class Task(TenantMixin, Base):
    __tablename__='tasks'
    title: Mapped[str] = mapped_column(String(140))
    application_id: Mapped[int | None] = mapped_column(ForeignKey('applications.id'), nullable=True)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    due_date: Mapped[str] = mapped_column(String(12), default='')

class TestDefinition(TenantMixin, Base):
    __tablename__='tests'
    title: Mapped[str] = mapped_column(String(120))
    questions: Mapped[list] = mapped_column(JSON, default=list)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    pass_percent: Mapped[int] = mapped_column(Integer, default=70)

class TestAttempt(TenantMixin, Base):
    __tablename__='test_attempts'
    test_id: Mapped[int] = mapped_column(ForeignKey('tests.id'))
    application_id: Mapped[int] = mapped_column(ForeignKey('applications.id'))
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    score: Mapped[float] = mapped_column(Float, default=0)

class JobApproval(TenantMixin, Base):
    __tablename__='job_approvals'
    job_id: Mapped[int] = mapped_column(ForeignKey('jobs.id'))
    approver_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(30), default='pending')
    comment: Mapped[str] = mapped_column(Text, default='')

class TalentList(TenantMixin, Base):
    __tablename__='talent_lists'
    name: Mapped[str] = mapped_column(String(100))
    candidate_ids: Mapped[list] = mapped_column(JSON, default=list)

Index('idx_application_tenant_stage',Application.company_id,Application.stage_id)

class Resume(TenantMixin, Base):
    __tablename__='resumes'
    candidate_id: Mapped[int] = mapped_column(ForeignKey('candidates.id'),index=True)
    filename: Mapped[str] = mapped_column(String(200))
    mime_type: Mapped[str] = mapped_column(String(120))
    storage_key: Mapped[str] = mapped_column(String(250))
    sha256: Mapped[str] = mapped_column(String(64))
    extracted_text: Mapped[str] = mapped_column(Text, default='')
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

# TalentFlow People: operational employee-lifecycle entities. The selection stage remains
# represented by Candidate/Application; employee records are a separate HRIS boundary.
class Employee(TenantMixin, Base):
    __tablename__='employees'
    __table_args__=(UniqueConstraint('company_id','employee_code'),)
    employee_code: Mapped[str] = mapped_column(String(36))
    name: Mapped[str] = mapped_column(String(200))
    work_email: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(100),default='Pessoas')
    job_title: Mapped[str] = mapped_column(String(160),default='')
    hire_date: Mapped[str] = mapped_column(String(10))
    exit_date: Mapped[str | None] = mapped_column(String(10),nullable=True)
    exit_kind: Mapped[str | None] = mapped_column(String(30),nullable=True)
    status: Mapped[str] = mapped_column(String(20),default='active')
    manager_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'),nullable=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey('applications.id'),nullable=True,unique=True)

class OnboardingItem(TenantMixin, Base):
    __tablename__='onboarding_items'
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'),index=True)
    title: Mapped[str] = mapped_column(String(160))
    phase: Mapped[str] = mapped_column(String(40),default='Primeira semana')
    due_date: Mapped[str | None] = mapped_column(String(10),nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True)

class LearningCourse(TenantMixin, Base):
    __tablename__='learning_courses'
    title: Mapped[str] = mapped_column(String(160))
    skill: Mapped[str] = mapped_column(String(120),default='')
    duration_hours: Mapped[float] = mapped_column(Float,default=1.0)
    active: Mapped[bool] = mapped_column(Boolean,default=True)

class LearningEnrollment(TenantMixin, Base):
    __tablename__='learning_enrollments'
    __table_args__=(UniqueConstraint('company_id','employee_id','course_id'),)
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'),index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey('learning_courses.id'))
    assigned_at: Mapped[str] = mapped_column(String(10))
    completed_at: Mapped[str | None] = mapped_column(String(10),nullable=True)
    status: Mapped[str] = mapped_column(String(20),default='assigned')

class PerformanceGoal(TenantMixin, Base):
    __tablename__='performance_goals'
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'),index=True)
    title: Mapped[str] = mapped_column(String(200))
    metric_unit: Mapped[str] = mapped_column(String(40),default='unidades')
    target_value: Mapped[float] = mapped_column(Float)
    actual_value: Mapped[float] = mapped_column(Float,default=0.0)
    due_date: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20),default='active')

class PerformanceReview(TenantMixin, Base):
    __tablename__='performance_reviews'
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'),index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    period: Mapped[str] = mapped_column(String(30))
    criteria: Mapped[list] = mapped_column(JSON,default=list)
    score: Mapped[float] = mapped_column(Float)
    feedback: Mapped[str] = mapped_column(Text,default='')

class CareerEvent(TenantMixin, Base):
    __tablename__='career_events'
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'),index=True)
    kind: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(Text)
    effective_on: Mapped[str] = mapped_column(String(10))

# Safeguards, lifecycle workflows (additive tables, no rewrite of existing demo records).
class RateLimitEvent(Base):
    __tablename__='rate_limit_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bucket_key: Mapped[str] = mapped_column(String(64),index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now,index=True)

class DevelopmentPlan(TenantMixin,Base):
    __tablename__='development_plans'
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'),index=True)
    title: Mapped[str] = mapped_column(String(180))
    competency: Mapped[str] = mapped_column(String(140),default='')
    goal: Mapped[str] = mapped_column(Text,default='')
    actions: Mapped[list] = mapped_column(JSON,default=list)
    progress: Mapped[int] = mapped_column(Integer,default=0)
    status: Mapped[str] = mapped_column(String(24),default='active')
    due_date: Mapped[str] = mapped_column(String(10))
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

class LeaveRequest(TenantMixin,Base):
    __tablename__='leave_requests'
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'),index=True)
    kind: Mapped[str] = mapped_column(String(30))
    starts_on: Mapped[str] = mapped_column(String(10))
    ends_on: Mapped[str] = mapped_column(String(10))
    days: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text,default='')
    status: Mapped[str] = mapped_column(String(20),default='pending')
    approver_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'),nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True)

Index('idx_dev_plan_company_employee',DevelopmentPlan.company_id,DevelopmentPlan.employee_id)
Index('idx_leave_company_status',LeaveRequest.company_id,LeaveRequest.status)
