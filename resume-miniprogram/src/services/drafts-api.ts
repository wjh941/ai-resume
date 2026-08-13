import { request } from "./http"
import type { JobIntelligence, ResumeDraft, ResumePayload, TemplateId } from "../types/resume"

type BackendDraft = {
  id: string
  client_id: string
  job_title: string
  template_id: TemplateId
  resume: ResumePayload
  job_intelligence: JobIntelligence | null
  created_at: string
  updated_at: string
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
    resume: item.resume,
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
