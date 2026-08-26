import { readItems, requestApi } from "./api"
import type { ResumePayload } from "./drafts"

export type EvidenceKind = "coursework" | "project" | "activity" | "internship" | "employment"

export type EvidenceRecord = {
  id: string
  clientId: string
  kind: EvidenceKind
  title: string
  context: string
  actions: string
  outcome: string
  proofNote: string
  verified: boolean
  createdAt: string
  updatedAt: string
}

export type EvidenceDraft = Omit<EvidenceRecord, "id" | "clientId" | "createdAt" | "updatedAt"> & { id?: string }

export type EvidenceSuggestion = {
  sourceEvidenceId: string
  sourceTitle: string
  targetSection: "project" | "employment"
  title: string
  role: string
  description: string
  riskNote: string
}

export type ResumeReadinessReport = {
  ready: boolean
  blockingItems: string[]
  warningItems: string[]
}

type BackendEvidence = {
  id: string
  client_id: string
  kind: EvidenceKind
  title: string
  context: string
  actions: string
  outcome: string
  proof_note: string
  verified: boolean
  created_at: string
  updated_at: string
}

type BackendSuggestion = {
  source_evidence_id: string
  source_title: string
  target_section: "project" | "employment"
  title: string
  role: string
  description: string
  risk_note: string
}

function fromEvidence(item: BackendEvidence): EvidenceRecord {
  return {
    id: item.id,
    clientId: item.client_id,
    kind: item.kind,
    title: item.title,
    context: item.context,
    actions: item.actions,
    outcome: item.outcome,
    proofNote: item.proof_note,
    verified: item.verified,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  }
}

function toEvidence(input: EvidenceDraft) {
  return {
    id: input.id,
    kind: input.kind,
    title: input.title,
    context: input.context,
    actions: input.actions,
    outcome: input.outcome,
    proof_note: input.proofNote,
    verified: input.verified,
  }
}

export async function listEvidence(): Promise<EvidenceRecord[]> {
  const payload = await requestApi<BackendEvidence[] | { items?: BackendEvidence[] }>("/api/evidence")
  return readItems(payload).map(fromEvidence)
}

export async function saveEvidence(input: EvidenceDraft): Promise<EvidenceRecord> {
  return fromEvidence(await requestApi<BackendEvidence>("/api/evidence", {
    method: "POST",
    body: JSON.stringify(toEvidence(input)),
  }))
}

export async function deleteEvidence(id: string): Promise<void> {
  await requestApi<{ id: string }>("/api/evidence/" + encodeURIComponent(id), { method: "DELETE" })
}

export async function getEvidenceSuggestions(roleName: string): Promise<EvidenceSuggestion[]> {
  const payload = await requestApi<BackendSuggestion[] | { items?: BackendSuggestion[] }>("/api/resume/evidence-suggestions", {
    method: "POST",
    body: JSON.stringify({ role_name: roleName }),
  })
  return readItems(payload).map((item) => ({
    sourceEvidenceId: item.source_evidence_id,
    sourceTitle: item.source_title,
    targetSection: item.target_section,
    title: item.title,
    role: item.role,
    description: item.description,
    riskNote: item.risk_note,
  }))
}

export async function checkResumeReadiness(resume: ResumePayload): Promise<ResumeReadinessReport> {
  const data = await requestApi<{ ready: boolean; blocking_items: string[]; warning_items: string[] }>(
    "/api/resume/readiness",
    {
      method: "POST",
      body: JSON.stringify({ resume: toBackendResume(resume) }),
    },
  )
  return {
    ready: data.ready,
    blockingItems: data.blocking_items,
    warningItems: data.warning_items,
  }
}

function toBackendResume(resume: ResumePayload) {
  return {
    version: 1,
    basic: resume.basic,
    job: {
      target_role: resume.job.targetRole,
      employment_type: resume.job.employmentType,
      expected_salary: resume.job.expectedSalary,
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
    section_visibility: {
      basic: resume.sectionVisibility.basic,
      job: resume.sectionVisibility.job,
      education: resume.sectionVisibility.education,
      employment: resume.sectionVisibility.employment,
      projects: resume.sectionVisibility.projects,
      skills: resume.sectionVisibility.skills,
      self_evaluation: resume.sectionVisibility.selfEvaluation,
    },
  }
}
