import { requestApi } from "./api"

export type ApplicationStatus = "saved" | "applied" | "screening" | "interview" | "offer" | "rejected" | "closed"

export type ApplicationTimelineEvent = {
  id: string
  title: string
  description: string
  occurredAt: string
}

export type ApplicationRecord = {
  id: string
  company: string
  roleName: string
  city: string
  source: string
  status: ApplicationStatus
  appliedAt: string | null
  nextActionAt: string | null
  interviewNotes: string
  draftId: string | null
  notes: string
  contactInfo: string
  attachmentRef: string
  nextInterviewAt: string | null
  timeline: ApplicationTimelineEvent[]
  createdAt: string
  updatedAt: string
}

export type ApplicationInput = Omit<ApplicationRecord, "createdAt" | "updatedAt" | "timeline">

export type ApplicationFilters = {
  status?: ApplicationStatus
  interviewDate?: string
}

type BackendTimeline = {
  id: string
  title: string
  description: string
  occurred_at: string
}

type BackendApplication = {
  id: string
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
  timeline?: BackendTimeline[]
  created_at: string
  updated_at: string
}

function fromTimeline(item: BackendTimeline): ApplicationTimelineEvent {
  return {
    id: item.id,
    title: item.title,
    description: item.description,
    occurredAt: item.occurred_at,
  }
}

function fromBackend(item: BackendApplication): ApplicationRecord {
  return {
    id: item.id,
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
    timeline: (item.timeline || []).map(fromTimeline),
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  }
}

function toBackend(input: ApplicationInput) {
  return {
    id: input.id,
    company: input.company,
    role_name: input.roleName,
    city: input.city,
    source: input.source,
    status: input.status,
    applied_at: input.appliedAt,
    next_action_at: input.nextActionAt,
    interview_notes: input.interviewNotes,
    draft_id: input.draftId,
    notes: input.notes,
    contact_info: input.contactInfo,
    attachment_ref: input.attachmentRef,
    next_interview_at: input.nextInterviewAt,
  }
}

export async function listApplications(filters: ApplicationFilters = {}): Promise<ApplicationRecord[]> {
  const params = new URLSearchParams()
  if (filters.status) params.set("status", filters.status)
  if (filters.interviewDate) params.set("interview_date", filters.interviewDate)
  const query = params.toString()
  const data = await requestApi<{ items: BackendApplication[] }>("/api/applications" + (query ? "?" + query : ""))
  return data.items.map(fromBackend)
}

export async function saveApplication(input: ApplicationInput): Promise<ApplicationRecord> {
  return fromBackend(await requestApi<BackendApplication>("/api/applications", {
    method: "POST",
    body: JSON.stringify(toBackend(input)),
  }))
}

export async function listTimeline(id: string): Promise<ApplicationTimelineEvent[]> {
  const data = await requestApi<{ items: BackendTimeline[] }>("/api/applications/" + encodeURIComponent(id) + "/timeline")
  return data.items.map(fromTimeline)
}

export async function addTimelineEvent(
  id: string,
  input: Omit<ApplicationTimelineEvent, "id">,
): Promise<ApplicationTimelineEvent> {
  return fromTimeline(await requestApi<BackendTimeline>("/api/applications/" + encodeURIComponent(id) + "/timeline", {
    method: "POST",
    body: JSON.stringify({
      title: input.title,
      description: input.description,
      occurred_at: input.occurredAt,
    }),
  }))
}

export async function saveReminder(id: string, reminderAt: string): Promise<void> {
  await requestApi("/api/applications/" + encodeURIComponent(id) + "/reminders", {
    method: "POST",
    body: JSON.stringify({ reminder_at: reminderAt }),
  })
}

export async function deleteApplication(id: string): Promise<void> {
  await requestApi<{ id: string }>("/api/applications/" + encodeURIComponent(id), { method: "DELETE" })
}
