export type Role = 'admin' | 'recruiter' | 'manager' | 'interviewer' | 'candidate';

export interface User { id: number; name: string; email: string; role: Role; company_id: number; company: string }

export interface Job {
  id: number; code: string; title: string; department: string; location: string; modality: string; seniority: string;
  employment: string; salary_min: number; salary_max: number; description: string; requirements: string; benefits: string;
  positions: number; status: 'open' | 'approval' | 'closed' | 'archived'; due_date: string; applications: number;
  version: number; created_at: string;
}
export interface Stage { id: number; name: string; kind: 'active' | 'hired' | 'rejected'; order: number }
export interface Candidate {
  id: number; name: string; email: string; phone: string; location: string; title: string; source: string;
  skills: string; experience_years: number; education: string; consent: boolean; created_at: string;
}
export interface ApplicationRow {
  id: number; candidate_id: number; job_id: number; stage_id: number; stage: string; status: string;
  fit: number; fit_reason: string; version: number; last_activity_at: string; applied_at: string; candidate: Candidate; job: Job;
}
export interface JobDetail { job: Job; stages: Stage[]; applications: ApplicationRow[] }

export interface Dashboard {
  metrics: {
    jobs_open: number; jobs_approval: number; candidates_active: number; hired: number; rejected: number;
    interviews: number; avg_time_hire: number; conversion: number; pending_tasks: number; late_jobs: number;
  };
  sources: { name: string; value: number }[];
  stages: { name: string; value: number }[];
  by_job: { name: string; value: number }[];
}

export interface Employee {
  id: number; name: string; employee_code: string; work_email: string; department: string; job_title: string;
  hire_date: string; exit_date: string | null; status: string;
}
export interface PlanAction { title: string; done: boolean; evidence: string }
export interface Plan {
  id: number; employee_id: number; employee: string; title: string; competency: string; goal: string;
  actions: PlanAction[]; progress: number; status: string; due_date: string; version: number;
}
export interface Leave {
  id: number; employee_id: number; employee: string; department: string; kind: string; starts_on: string;
  ends_on: string; days: number; reason: string; status: 'pending' | 'approved' | 'rejected'; decided_at: string | null;
}
export interface Insights {
  population: number; active: number; pending_leaves: number; plan_count: number; completed_plans: number;
  development_completion: { numerator: number; denominator: number; interpretation: string };
  departments: { name: string; count: number | null; suppressed: boolean }[]; limits: string[];
}
export interface SessionInfo { id: string; client: string; kind: string; expires_at: string; current: boolean }
export interface Changes { cursor: number; latest: number; has_more: boolean; entities: string[]; items: { seq: number; entity: string; action: string }[] }
