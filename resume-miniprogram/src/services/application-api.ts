import { request } from "./http"
import type {
  ApplicationInput,
  ApplicationRecord,
  ApplicationStatus,
  ApplicationTimelineEvent,
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
  contact_info?: string
  attachment_ref?: string
  next_interview_at?: string | null
  timeline?: Array<{ id: string; title: string; description: string; occurred_at: string }>
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
    contactInfo: item.contact_info || "",
    attachmentRef: item.attachment_ref || "",
    nextInterviewAt: item.next_interview_at || null,
    timeline: (item.timeline || []).map(fromTimelineEvent),
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
    contact_info: item.contactInfo || "",
    attachment_ref: item.attachmentRef || "",
    next_interview_at: item.nextInterviewAt || null,
  }
}

export async function listApplications(
  clientId: string,
  status?: ApplicationStatus,
  interviewDate?: string,
): Promise<ApplicationRecord[]> {
  const params = new URLSearchParams({ client_id: clientId })
  if (status) params.set("status", status)
  if (interviewDate) params.set("interview_date", interviewDate)
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

function fromTimelineEvent(item: {
  id: string
  title: string
  description: string
  occurred_at: string
}): ApplicationTimelineEvent {
  return {
    id: item.id,
    title: item.title,
    description: item.description,
    occurredAt: item.occurred_at,
  }
}

export async function listApplicationTimeline(applicationId: string): Promise<ApplicationTimelineEvent[]> {
  const data = await request<{ items: Array<{ id: string; title: string; description: string; occurred_at: string }> }>(
    `/api/applications/${encodeURIComponent(applicationId)}/timeline`,
  )
  return data.items.map(fromTimelineEvent)
}

export async function createApplicationTimelineEvent(
  applicationId: string,
  event: Omit<ApplicationTimelineEvent, "id">,
): Promise<ApplicationTimelineEvent> {
  const data = await request<{ id: string; title: string; description: string; occurred_at: string }>(
    `/api/applications/${encodeURIComponent(applicationId)}/timeline`,
    "POST",
    { title: event.title, description: event.description, occurred_at: event.occurredAt },
  )
  return fromTimelineEvent(data)
}

export async function saveInterviewReminder(applicationId: string, reminderAt: string): Promise<void> {
  await request(
    `/api/applications/${encodeURIComponent(applicationId)}/reminders`,
    "POST",
    { reminder_at: reminderAt },
  )
}
