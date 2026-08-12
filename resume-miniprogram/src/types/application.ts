export type ApplicationStatus =
  | "saved"
  | "applied"
  | "screening"
  | "interview"
  | "offer"
  | "rejected"
  | "closed"

export type ApplicationInput = {
  id?: string
  clientId: string
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
}

export type ApplicationRecord = ApplicationInput & {
  id: string
  createdAt: string
  updatedAt: string
}

export type PendingApplication = ApplicationInput & {
  localId: string
}
