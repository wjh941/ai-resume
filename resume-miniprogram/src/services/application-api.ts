import { request } from "./http"
import type {
  ApplicationInput,
  ApplicationRecord,
  ApplicationStatus,
} from "../types/application"

type BackendApplication = {
  id: string
  client_id: string
  company: string
  role_name: string
  city: string
  source: string
  status: ApplicationStatus
  applied_at: string | null
  next_action_at: string | null
  interview_notes: string
  draft_id: string | null
  notes: string
  created_at: string
  updated_at: string
}

function fromBackend(item: BackendApplication): ApplicationRecord {
  return {
    id: item.id,
    clientId: item.client_id,
    company: item.company,
    roleName: item.role_name,
    city: item.city,
    source: item.source,
    status: item.status,
    appliedAt: item.applied_at,
    nextActionAt: item.next_action_at,
    interviewNotes: item.interview_notes,
    draftId: item.draft_id,
    notes: item.notes,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  }
}

function toBackend(item: ApplicationInput) {
  return {
    id: item.id,
    client_id: item.clientId,
    company: item.company,
    role_name: item.roleName,
    city: item.city,
    source: item.source,
    status: item.status,
    applied_at: item.appliedAt,
    next_action_at: item.nextActionAt,
    interview_notes: item.interviewNotes,
    draft_id: item.draftId,
    notes: item.notes,
  }
}

export async function listApplications(
  clientId: string,
  status?: ApplicationStatus,
): Promise<ApplicationRecord[]> {
  const params = new URLSearchParams({ client_id: clientId })
  if (status) params.set("status", status)
  const data = await request<{ items: BackendApplication[] }>(`/api/applications?${params}`)
  return data.items.map(fromBackend)
}

export async function saveApplication(input: ApplicationInput): Promise<ApplicationRecord> {
  return fromBackend(
    await request<BackendApplication>("/api/applications", "POST", toBackend(input)),
  )
}

export async function deleteApplication(clientId: string, applicationId: string): Promise<void> {
  await request<{ id: string }>(
    `/api/applications/${encodeURIComponent(applicationId)}?client_id=${encodeURIComponent(clientId)}`,
    "DELETE",
  )
}
