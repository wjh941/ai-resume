import { request } from "./http"
import type { JobIntelligence, ResumeDraft, ResumePayload, TemplateId } from "../types/resume"

type BackendResume = {
  version: 1
  basic: ResumePayload["basic"]
  job: { target_role: string; expected_salary: string; employment_type: string }
  education: Array<{
    school: string; major: string; degree: string; start_date: string; end_date: string; courses: string
  }>
  employment: Array<{
    company: string; position: string; start_date: string; end_date: string; description: string
  }>
  projects: Array<{
    name: string; role: string; start_date: string; end_date: string; description: string
  }>
  skills: { skills: string[]; certificates: string[]; english_level: string }
  self_evaluation: string
  section_visibility: {
    basic: boolean; job: boolean; education: boolean; employment: boolean
    projects: boolean; skills: boolean; self_evaluation: boolean
  }
}

type BackendDraft = {
  id: string
  client_id: string
  job_title: string
  template_id: TemplateId
  resume: BackendResume
  job_intelligence: JobIntelligence | null
  created_at: string
  updated_at: string
}

function fromBackendResume(resume: BackendResume): ResumePayload {
  return {
    version: resume.version,
    basic: {
      name: resume.basic.name,
      phone: resume.basic.phone,
      email: resume.basic.email,
      city: resume.basic.city,
      gender: resume.basic.gender,
    },
    job: {
      targetRole: resume.job.target_role,
      expectedSalary: resume.job.expected_salary,
      availability: resume.job.employment_type,
    },
    education: resume.education.map((item) => ({
      school: item.school,
      major: item.major,
      degree: item.degree,
      startDate: item.start_date,
      endDate: item.end_date,
      courses: item.courses,
    })),
    employment: resume.employment.map((item) => ({
      company: item.company,
      position: item.position,
      startDate: item.start_date,
      endDate: item.end_date,
      description: item.description,
    })),
    projects: resume.projects.map((item) => ({
      name: item.name,
      role: item.role,
      startDate: item.start_date,
      endDate: item.end_date,
      description: item.description,
    })),
    skills: {
      skills: resume.skills.skills,
      certificates: resume.skills.certificates,
      englishLevel: resume.skills.english_level,
    },
    selfEvaluation: resume.self_evaluation,
    sectionVisibility: {
      basic: resume.section_visibility.basic,
      job: resume.section_visibility.job,
      education: resume.section_visibility.education,
      employment: resume.section_visibility.employment,
      projects: resume.section_visibility.projects,
      skills: resume.section_visibility.skills,
      selfEvaluation: resume.section_visibility.self_evaluation,
    },
  }
}

export type DraftRecord = {
  id: string
  clientId: string
  jobTitle: string
  templateId: TemplateId
  resume: ResumePayload
  jobIntelligence: JobIntelligence | null
  createdAt: string
  updatedAt: string
}

function fromBackend(item: BackendDraft): DraftRecord {
  return {
    id: item.id,
    clientId: item.client_id,
    jobTitle: item.job_title,
    templateId: item.template_id,
    resume: fromBackendResume(item.resume),
    jobIntelligence: item.job_intelligence,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  }
}

export function toResumeDraft(record: DraftRecord): ResumeDraft {
  return {
    id: record.id,
    jobTitle: record.jobTitle,
    templateId: record.templateId,
    resume: record.resume,
    jobIntelligence: record.jobIntelligence,
  }
}

export async function listDrafts(clientId: string): Promise<DraftRecord[]> {
  const items = await request<BackendDraft[]>(`/api/draft/list?client_id=${encodeURIComponent(clientId)}`)
  return items.map(fromBackend)
}

export async function getDraft(clientId: string, draftId: string): Promise<DraftRecord> {
  return fromBackend(await request<BackendDraft>(
    `/api/draft/${encodeURIComponent(draftId)}?client_id=${encodeURIComponent(clientId)}`,
  ))
}

export async function copyDraft(clientId: string, draftId: string): Promise<DraftRecord> {
  return fromBackend(await request<BackendDraft>(
    `/api/draft/${encodeURIComponent(draftId)}/copy`,
    "POST",
    { client_id: clientId },
  ))
}

export async function deleteDraft(clientId: string, draftId: string): Promise<void> {
  await request<{ id: string }>(
    `/api/draft/${encodeURIComponent(draftId)}?client_id=${encodeURIComponent(clientId)}`,
    "DELETE",
  )
}
