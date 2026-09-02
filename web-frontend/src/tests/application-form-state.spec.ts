import { describe, expect, it } from "vitest"

import {
  createApplicationFormSnapshot,
  isApplicationFormDirty,
  type ApplicationFormValues,
  type ApplicationTimelineValues,
} from "../lib/application-form-state"

const form = (): ApplicationFormValues => ({
  company: "Acme",
  roleName: "Product Designer",
  city: "Shanghai",
  status: "saved",
  source: "Referral",
  appliedAt: "2026-09-01",
  nextActionAt: "2026-09-05",
  nextInterviewAt: "2026-09-08T10:00",
  interviewNotes: "Portfolio walkthrough",
  notes: "Follow up after interview",
  contactInfo: "recruiter@acme.example",
  attachmentRef: "portfolio.pdf",
  draftId: "draft-1",
})

const timeline = (): ApplicationTimelineValues => ({
  title: "Phone screen",
  description: "Discussed role scope",
  occurredAt: "2026-09-02T09:00",
})

const snapshot = () => createApplicationFormSnapshot(form(), timeline(), "2026-09-04T09:00")

describe("application form snapshots", () => {
  it("treats identical snapshots as clean", () => {
    expect(isApplicationFormDirty(snapshot(), snapshot())).toBe(false)
  })

  it("detects a changed main form field", () => {
    const current = snapshot()
    current.form.company = "Globex"

    expect(isApplicationFormDirty(current, snapshot())).toBe(true)
  })

  it("detects a changed timeline field", () => {
    const current = snapshot()
    current.timeline.title = "Onsite interview"

    expect(isApplicationFormDirty(current, snapshot())).toBe(true)
  })

  it("detects a changed reminder time", () => {
    const current = snapshot()
    current.reminderAt = "2026-09-06T09:00"

    expect(isApplicationFormDirty(current, snapshot())).toBe(true)
  })

  it("keeps the baseline isolated from source object mutations", () => {
    const sourceForm = form()
    const sourceTimeline = timeline()
    const baseline = createApplicationFormSnapshot(sourceForm, sourceTimeline, "2026-09-04T09:00")

    sourceForm.company = "Mutated after snapshot"
    sourceTimeline.title = "Mutated timeline"

    expect(baseline.form.company).toBe("Acme")
    expect(baseline.timeline.title).toBe("Phone screen")
    expect(baseline.reminderAt).toBe("2026-09-04T09:00")
  })
})
