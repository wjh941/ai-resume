import { describe, expect, it } from "vitest"

import { appendTimelineEvent, removeApplication, replaceApplication } from "../lib/application-workflow"
import type { ApplicationRecord } from "../lib/applications"

const record = (id: string, status: ApplicationRecord["status"] = "saved"): ApplicationRecord => ({
  id,
  company: "示例科技",
  roleName: "产品运营",
  city: "上海",
  source: "",
  status,
  appliedAt: null,
  nextActionAt: null,
  interviewNotes: "",
  draftId: null,
  notes: "",
  contactInfo: "",
  attachmentRef: "",
  nextInterviewAt: null,
  timeline: [],
  createdAt: "t1",
  updatedAt: "t1",
})

describe("application workflow helpers", () => {
  it("replaces only the saved application row", () => {
    expect(replaceApplication([record("a-1"), record("a-2")], record("a-1", "interview"))[0].status).toBe("interview")
  })

  it("appends a timeline event without mutating the source record", () => {
    const original = record("a-1")
    const updated = appendTimelineEvent(original, { id: "e-1", title: "完成一面", description: "", occurredAt: "t2" })
    expect(updated.timeline).toHaveLength(1)
    expect(original.timeline).toHaveLength(0)
  })

  it("removes only the confirmed application", () => {
    expect(removeApplication([record("a-1"), record("a-2")], "a-1").map((item) => item.id)).toEqual(["a-2"])
  })
})
