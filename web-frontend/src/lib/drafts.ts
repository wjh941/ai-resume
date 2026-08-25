import { requestApi } from "./api"

export type TemplateId = "business" | "technology" | "graduate" | "analytics"

export type ResumePayload = {
  version: 1
  basic: { name: string; phone: string; email: string; city: string }
  job: { targetRole: string; expectedSalary: string; employmentType: string }
  education: Array<{ school: string; major: string; degree: string; startDate: string; endDate: string }>
  employment: Array<{ company: string; position: string; startDate: string; endDate: string; description: string }>
  projects: Array<{ name: string; role: string; startDate: string; endDate: string; description: string }>
  skills: { skills: string[]; certificates: string[] }
  selfEvaluation: string
  sectionVisibility: Record<"basic" | "job" | "education" | "employment" | "projects" | "skills" | "selfEvaluation", boolean>
}

export type DraftRecord = {
  id: string
  jobTitle: string
  templateId: TemplateId
  resume: ResumePayload
  jobIntelligence: Record<string, unknown> | null
  createdAt: string
  updatedAt: string
}

export type DraftSaveInput = Omit<DraftRecord, "createdAt" | "updatedAt">

type BackendResume = {
  version: 1
  basic: ResumePayload["basic"]
  job: { target_role: string; expected_salary: string; employment_type: string }
  education: Array<{ school: string; major: string; degree: string; start_date: string; end_date: string }>
  employment: Array<{ company: string; position: string; start_date: string; end_date: string; description: string }>
  projects: Array<{ name: string; role: string; start_date: string; end_date: string; description: string }>
  skills: { skills: string[]; certificates: string[] }
  self_evaluation: string
  section_visibility: Record<"basic" | "job" | "education" | "employment" | "projects" | "skills" | "self_evaluation", boolean>
}

type BackendDraft = {
  id: string
  job_title: string
  template_id: TemplateId
  resume: BackendResume
  job_intelligence: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

function fromResume(resume: BackendResume): ResumePayload {
  const job = resume.job || { target_role: "", expected_salary: "", employment_type: "" }
  return {
    version: 1,
    basic: resume.basic || { name: "", phone: "", email: "", city: "" },
    job: {
      targetRole: job.target_role,
      expectedSalary: job.expected_salary,
      employmentType: job.employment_type,
    },
    education: (resume.education || []).map((item) => ({
      school: item.school,
      major: item.major,
      degree: item.degree,
      startDate: item.start_date,
      endDate: item.end_date,
    })),
    employment: (resume.employment || []).map((item) => ({
      company: item.company,
      position: item.position,
      startDate: item.start_date,
      endDate: item.end_date,
      description: item.description,
    })),
    projects: (resume.projects || []).map((item) => ({
      name: item.name,
      role: item.role,
      startDate: item.start_date,
      endDate: item.end_date,
      description: item.description,
    })),
    skills: resume.skills || { skills: [], certificates: [] },
    selfEvaluation: resume.self_evaluation || "",
    sectionVisibility: resume.section_visibility || {
      basic: true, job: true, education: true, employment: true,
      projects: true, skills: true, selfEvaluation: true,
    },
  }
}

function toResume(resume: ResumePayload): BackendResume {
  return {
    version: 1,
    basic: resume.basic,
    job: {
      target_role: resume.job.targetRole,
      expected_salary: resume.job.expectedSalary,
      employment_type: resume.job.employmentType,
    },
    education: resume.education.map((item) => ({
      school: item.school,
      major: item.major,
      degree: item.degree,
      start_date: item.startDate,
      end_date: item.endDate,
    })),
    employment: resume.employment.map((item) => ({
      company: item.company,
      position: item.position,
      start_date: item.startDate,
      end_date: item.endDate,
      description: item.description,
    })),
    projects: resume.projects.map((item) => ({
      name: item.name,
      role: item.role,
      start_date: item.startDate,
      end_date: item.endDate,
      description: item.description,
    })),
    skills: resume.skills,
    self_evaluation: resume.selfEvaluation,
    section_visibility: resume.sectionVisibility,
  }
}

function fromBackend(item: BackendDraft): DraftRecord {
  return {
    id: item.id,
    jobTitle: item.job_title,
    templateId: item.template_id,
    resume: fromResume(item.resume),
    jobIntelligence: item.job_intelligence,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  }
}

export async function listDrafts(): Promise<DraftRecord[]> {
  const data = await requestApi<{ items: BackendDraft[] } | BackendDraft[]>("/api/draft/list")
  return (Array.isArray(data) ? data : data.items).map(fromBackend)
}

export async function getDraft(id: string): Promise<DraftRecord> {
  return fromBackend(await requestApi<BackendDraft>("/api/draft/" + encodeURIComponent(id)))
}

export async function saveDraft(input: DraftSaveInput): Promise<DraftRecord> {
  const data = await requestApi<BackendDraft>("/api/draft/save", {
    method: "POST",
    body: JSON.stringify({
      id: input.id,
      job_title: input.jobTitle,
      template_id: input.templateId,
      resume: toResume(input.resume),
      job_intelligence: input.jobIntelligence,
    }),
  })
  return fromBackend(data)
}

export async function copyDraft(id: string): Promise<DraftRecord> {
  return fromBackend(await requestApi<BackendDraft>("/api/draft/" + encodeURIComponent(id) + "/copy", {
    method: "POST",
    body: JSON.stringify({}),
  }))
}

export async function deleteDraft(id: string): Promise<void> {
  await requestApi<{ id: string }>("/api/draft/" + encodeURIComponent(id), { method: "DELETE" })
}
