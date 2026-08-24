import { describe, expect, it } from "vitest"

import type { DraftRecord } from "../lib/drafts"
import { validateDraft } from "../lib/resume-validation"

const validDraft = (): DraftRecord => ({
  id: "d-1",
  jobTitle: "数据工程师简历",
  templateId: "business",
  resume: {
    version: 1,
    basic: { name: "张三", phone: "13800138000", email: "zhang@example.com", city: "上海" },
    job: { targetRole: "数据工程师", expectedSalary: "", employmentType: "" },
    education: [], employment: [], projects: [],
    skills: { skills: [], certificates: [] }, selfEvaluation: "",
    sectionVisibility: { basic: true, job: true, education: true, employment: true, projects: true, skills: true, selfEvaluation: true },
  },
  jobIntelligence: null,
  createdAt: "2026-08-24T09:00:00Z",
  updatedAt: "2026-08-24T10:00:00Z",
})

describe("validateDraft", () => {
  it("returns no errors for a valid draft", () => {
    expect(validateDraft(validDraft())).toEqual({})
  })

  it("returns every aligned required-field key", () => {
    const draft = validDraft()
    draft.jobTitle = ""
    draft.resume.basic = { name: "", phone: "123", email: "bad", city: "" }
    draft.resume.job.targetRole = ""
    expect(Object.keys(validateDraft(draft))).toEqual(expect.arrayContaining([
      "jobTitle", "basic.name", "basic.phone", "basic.email", "job.targetRole",
    ]))
  })
})
