import { describe, expect, it } from "vitest"

import { createEmptyDraftInput } from "../lib/resume-draft"

describe("createEmptyDraftInput", () => {
  it("creates a complete empty draft with the selected title and template", () => {
    const draft = createEmptyDraftInput("数据分析师", "analytics")

    expect(draft).toMatchObject({ id: "", jobTitle: "数据分析师", templateId: "analytics" })
    expect(draft.resume.basic).toEqual({ name: "", phone: "", email: "", city: "" })
    expect(draft.resume.job).toEqual({ targetRole: "数据分析师", expectedSalary: "", employmentType: "" })
    expect(draft.resume.education).toEqual([])
    expect(draft.resume.employment).toEqual([])
    expect(draft.resume.projects).toEqual([])
    expect(draft.resume.skills).toEqual({ skills: [], certificates: [] })
    expect(draft.resume.sectionVisibility).toEqual({
      basic: true,
      job: true,
      education: true,
      employment: true,
      projects: true,
      skills: true,
      selfEvaluation: true,
    })
  })

  it("normalizes a blank title without changing the selected template", () => {
    const draft = createEmptyDraftInput("  ", "business")

    expect(draft.jobTitle).toBe("未命名简历")
    expect(draft.resume.job.targetRole).toBe("")
  })
})
