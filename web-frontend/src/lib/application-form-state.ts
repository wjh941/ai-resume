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
    form: {
      company: form.company,
      roleName: form.roleName,
      city: form.city,
      status: form.status,
      source: form.source,
      appliedAt: form.appliedAt,
      nextActionAt: form.nextActionAt,
      nextInterviewAt: form.nextInterviewAt,
      interviewNotes: form.interviewNotes,
      notes: form.notes,
      contactInfo: form.contactInfo,
      attachmentRef: form.attachmentRef,
      draftId: form.draftId,
    },
    timeline: {
      title: timeline.title,
      description: timeline.description,
      occurredAt: timeline.occurredAt,
    },
    reminderAt,
  }
}

export function isApplicationFormDirty(
  current: ApplicationFormSnapshot,
  baseline: ApplicationFormSnapshot,
): boolean {
  return JSON.stringify(current) !== JSON.stringify(baseline)
}
