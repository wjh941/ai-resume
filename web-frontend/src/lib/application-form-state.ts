export interface ApplicationFormValues {
  company: string
  roleName: string
  city: string
  status: string
  source: string
  appliedAt: string
  nextActionAt: string
  nextInterviewAt: string
  interviewNotes: string
  notes: string
  contactInfo: string
  attachmentRef: string
  draftId: string
}

export interface ApplicationTimelineValues {
  title: string
  description: string
  occurredAt: string
}

export interface ApplicationFormSnapshot {
  form: ApplicationFormValues
  timeline: ApplicationTimelineValues
  reminderAt: string
}

export function createApplicationFormSnapshot(
  form: ApplicationFormValues,
  timeline: ApplicationTimelineValues,
  reminderAt: string,
): ApplicationFormSnapshot {
  return {
    form: { ...form },
    timeline: { ...timeline },
    reminderAt,
  }
}

export function isApplicationFormDirty(
  current: ApplicationFormSnapshot,
  baseline: ApplicationFormSnapshot,
): boolean {
  return JSON.stringify(current) !== JSON.stringify(baseline)
}
