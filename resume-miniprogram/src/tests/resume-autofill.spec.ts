import { describe, expect, it } from "vitest"

import { createEmptyDraft, type JobIntelligence } from "../types/resume"
import {
  createRoleBasedInternshipDraft,
  prepareResumeForJob,
} from "../utils/resume-autofill"

const frontendJob: JobIntelligence = {
  version: 1,
  roleName: "前端开发工程师",
  salaryByExperience: {
    graduate: "12k-18k",
    "1-3_years": "18k-30k",
    "3-5_years": "30k-45k",
    "5_plus_years": "45k-65k",
  },
  responsibilities: [
    "Build responsive interfaces and reusable component systems.",
    "Collaborate with product and design teams to improve web experiences.",
  ],
  hardRequirements: ["Bachelor degree or equivalent practical experience."],
  requiredSkills: ["JavaScript", "TypeScript", "Vue or React"],
  bonusSkills: ["Vite", "State management", "Frontend performance"],
  careerRoute: ["Frontend Engineer", "Senior Frontend Engineer", "Frontend Architect"],
}

describe("prepareResumeForJob", () => {
  it("fills only blank non-factual fields from the selected job", () => {
    const draft = createEmptyDraft()
    draft.resume.basic.name = "张三"

    prepareResumeForJob(draft, frontendJob)

    expect(draft.jobTitle).toBe("前端开发工程师")
    expect(draft.resume.job.targetRole).toBe("前端开发工程师")
    expect(draft.resume.job.expectedSalary).toBe("18k-30k")
    expect(draft.resume.skills.skills).toEqual([
      "JavaScript（待确认）",
      "TypeScript（待确认）",
      "Vue or React（待确认）",
    ])
    expect(draft.resume.basic.name).toBe("张三")
    expect(draft.resume.education).toEqual([])
    expect(draft.resume.employment).toEqual([])
    expect(draft.resume.projects).toHaveLength(1)
    expect(draft.resume.projects[0].name).toContain("[待确认]")
    expect(draft.resume.projects[0].description).toContain("TypeScript")
    expect(draft.resume.projects[0].description).toContain("真实业务场景")
  })

  it("does not overwrite fields the user already completed", () => {
    const draft = createEmptyDraft()
    draft.resume.job.expectedSalary = "20k-25k"
    draft.resume.skills.skills = ["Python"]
    draft.resume.selfEvaluation = "已有自我评价"

    prepareResumeForJob(draft, frontendJob)

    expect(draft.resume.job.expectedSalary).toBe("20k-25k")
    expect(draft.resume.skills.skills).toEqual(["Python"])
    expect(draft.resume.selfEvaluation).toBe("已有自我评价")
  })

  it("creates an optional internship draft with explicit unknown company and dates", () => {
    const draft = createRoleBasedInternshipDraft(frontendJob)

    expect(draft.company).toContain("[待确认]")
    expect(draft.startDate).toContain("[待确认]")
    expect(draft.endDate).toContain("[待确认]")
    expect(draft.description).toContain("Vue or React")
  })
})
