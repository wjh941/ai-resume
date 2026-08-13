import { beforeEach, describe, expect, it } from "vitest"

import { listDrafts, toResumeDraft } from "../services/drafts-api"

beforeEach(() => {
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async () => ({
      statusCode: 200,
      data: {
        code: "ok",
        data: [{
          id: "draft-1",
          client_id: "client-a",
          job_title: "Data Engineer",
          template_id: "technology",
          resume: {
            version: 1,
            basic: { name: "Alice", phone: "123", email: "a@example.com", city: "Shanghai", gender: "" },
            job: { target_role: "Data Engineer", expected_salary: "20k", employment_type: "full-time" },
            education: [{ school: "Uni", major: "CS", degree: "Bachelor", start_date: "2020", end_date: "2024", courses: "SQL" }],
            employment: [{ company: "Acme", position: "Analyst", start_date: "2024-01", end_date: "2025-01", description: "Built reports" }],
            projects: [{ name: "Pipeline", role: "Owner", start_date: "2024-02", end_date: "2024-06", description: "Shipped it" }],
            skills: { skills: ["SQL"], certificates: ["AWS"], english_level: "C1" },
            self_evaluation: "Careful",
            section_visibility: {
              basic: true, job: false, education: true, employment: true,
              projects: false, skills: true, self_evaluation: false,
            },
          },
          job_intelligence: null,
          created_at: "2026-08-13T00:00:00+00:00",
          updated_at: "2026-08-13T00:00:00+00:00",
        }],
      },
    }),
  }
})

describe("draft API resume mapping", () => {
  it("maps snake_case backend resume fields into the frontend draft shape", async () => {
    const [record] = await listDrafts("client-a")
    const draft = toResumeDraft(record)

    expect(draft.resume.job.targetRole).toBe("Data Engineer")
    expect(draft.resume.education[0].startDate).toBe("2020")
    expect(draft.resume.employment[0].endDate).toBe("2025-01")
    expect(draft.resume.projects[0].startDate).toBe("2024-02")
    expect(draft.resume.skills.englishLevel).toBe("C1")
    expect(draft.resume.selfEvaluation).toBe("Careful")
    expect(draft.resume.sectionVisibility).toEqual({
      basic: true, job: false, education: true, employment: true,
      projects: false, skills: true, selfEvaluation: false,
    })
  })
})
