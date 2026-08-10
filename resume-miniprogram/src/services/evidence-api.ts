import { request } from "./http"
import type { ResumePayload } from "../types/resume"
import type {
  EvidenceSuggestion,
  ResumeEvidence,
  ResumeEvidenceInput,
  ResumeReadinessReport,
} from "../types/evidence"


type BackendEvidence = {
  id: string
  client_id: string
  kind: ResumeEvidence["kind"]
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
  target_section: EvidenceSuggestion["targetSection"]
  title: string
  role: string
  description: string
  risk_note: string
}

type BackendReadiness = {
  ready: boolean
  blocking_items: string[]
  warning_items: string[]
}


function fromBackendEvidence(evidence: BackendEvidence): ResumeEvidence {
  return {
    id: evidence.id,
    clientId: evidence.client_id,
    kind: evidence.kind,
    title: evidence.title,
    context: evidence.context,
    actions: evidence.actions,
    outcome: evidence.outcome,
    proofNote: evidence.proof_note,
    verified: evidence.verified,
    createdAt: evidence.created_at,
    updatedAt: evidence.updated_at,
  }
}


function fromBackendSuggestion(suggestion: BackendSuggestion): EvidenceSuggestion {
  return {
    sourceEvidenceId: suggestion.source_evidence_id,
    sourceTitle: suggestion.source_title,
    targetSection: suggestion.target_section,
    title: suggestion.title,
    role: suggestion.role,
    description: suggestion.description,
    riskNote: suggestion.risk_note,
  }
}


function toBackendEvidence(evidence: ResumeEvidenceInput) {
  return {
    id: evidence.id,
    client_id: evidence.clientId,
    kind: evidence.kind,
    title: evidence.title,
    context: evidence.context,
    actions: evidence.actions,
    outcome: evidence.outcome,
    proof_note: evidence.proofNote,
    verified: evidence.verified,
  }
}


function toBackendResume(resume: ResumePayload) {
  return {
    version: 1,
    basic: resume.basic,
    job: {
      target_role: resume.job.targetRole,
      employment_type: resume.job.availability,
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


export async function listEvidence(clientId: string): Promise<ResumeEvidence[]> {
  const response = await request<{ items: BackendEvidence[] }>(
    `/api/evidence?client_id=${encodeURIComponent(clientId)}`,
  )
  return response.items.map(fromBackendEvidence)
}


export async function saveEvidence(evidence: ResumeEvidenceInput): Promise<ResumeEvidence> {
  const response = await request<BackendEvidence>(
    "/api/evidence",
    "POST",
    toBackendEvidence(evidence),
  )
  return fromBackendEvidence(response)
}


export async function deleteEvidence(clientId: string, evidenceId: string): Promise<void> {
  await request<{ id: string }>(
    `/api/evidence/${encodeURIComponent(evidenceId)}?client_id=${encodeURIComponent(clientId)}`,
    "DELETE",
  )
}


export async function getEvidenceSuggestions(
  clientId: string,
  roleName: string,
): Promise<EvidenceSuggestion[]> {
  const response = await request<{ items: BackendSuggestion[] }>(
    "/api/resume/evidence-suggestions",
    "POST",
    { client_id: clientId, role_name: roleName },
  )
  return response.items.map(fromBackendSuggestion)
}


export async function checkResumeReadiness(
  resume: ResumePayload,
): Promise<ResumeReadinessReport> {
  const response = await request<BackendReadiness>(
    "/api/resume/readiness",
    "POST",
    { resume: toBackendResume(resume) },
  )
  return {
    ready: response.ready,
    blockingItems: response.blocking_items,
    warningItems: response.warning_items,
  }
}
