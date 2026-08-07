import { beforeEach, describe, expect, it } from "vitest"

import { queryJobConsultation, reviewResumeText } from "../services/resume-api"

type CapturedRequest = { url: string; data?: unknown }

const calls: CapturedRequest[] = []

beforeEach(() => {
  calls.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async (options: Record<string, unknown>) => {
      calls.push({ url: String(options.url), data: options.data })
      if (String(options.url).endsWith("/api/consultation/job-analysis")) {
        return {
          statusCode: 200,
          data: {
            code: "ok",
            data: {
              identity_code: "2",
              identity_label: "Graduate",
              job_intelligence: {
                version: 1,
                role_name: "Data Engineer",
                salary_by_experience: {},
                responsibilities: [],
                hard_requirements: [],
                required_skills: ["Python"],
                bonus_skills: [],
                career_route: [],
              },
              job_analysis_sections: Array.from({ length: 9 }, (_, index) => ({
                order: index + 1,
                title: `Section ${index + 1}`,
                items: ["Item"],
              })),
              identity_plan: {
                title: "Graduate plan",
                sections: Array.from({ length: 4 }, (_, index) => ({
                  order: index + 1,
                  title: `Plan ${index + 1}`,
                  items: ["Item"],
                })),
              },
              follow_up_question: "Question",
              market_notice: "Estimate",
              career_growth_route: {
                title: "Career Growth Route",
                stages: [
                  {
                    stage: "Junior",
                    role_name: "Junior Data Engineer",
                    years_reference: "0-2",
                    core_skills: ["Python"],
                    responsibilities: ["Deliver"],
                    assessment_criteria: ["Pass review"],
                  },
                  {
                    stage: "Mid-level",
                    role_name: "Data Engineer",
                    years_reference: "2-5",
                    core_skills: ["SQL"],
                    responsibilities: ["Own module"],
                    assessment_criteria: ["Own delivery"],
                  },
                  {
                    stage: "Senior",
                    role_name: "Senior Data Engineer",
                    years_reference: "5+",
                    core_skills: ["Architecture"],
                    responsibilities: ["Lead"],
                    assessment_criteria: ["Influence"],
                  },
                ],
              },
              custom_requirement_notes: ["Applied: Hangzhou"],
            },
          },
        }
      }
      return {
        statusCode: 200,
        data: {
          code: "ok",
          data: {
            identity_code: "2",
            identity_label: "Graduate",
            issues: ["Issue"],
            rewrite_examples: ["Rewrite"],
            keywords: ["Python"],
            optimized_resume_text: "Draft [待确认]",
            interview_intro: "Introduction",
            job_match_report: {
              score: 60,
              score_basis: ["Coverage"],
              matching_advantages: ["SQL"],
              missing_skills: ["Python"],
              priority_gaps: [
                {
                  skill_name: "Python",
                  learning_direction: "Learn fundamentals",
                  project_practice: "Build project",
                  practice_task: "Practice",
                },
              ],
            },
            custom_requirement_notes: ["Applied: Entry-level"],
          },
        },
      }
    },
  }
})

describe("consultation API mapping", () => {
  it("maps the career growth route and forwards the supplementary job requirement", async () => {
    const result = await queryJobConsultation("Data Engineer", "2", "Prefer Hangzhou")

    expect(result.careerGrowthRoute.stages).toHaveLength(3)
    expect(result.careerGrowthRoute.stages[2].roleName).toBe("Senior Data Engineer")
    expect(result.customRequirementNotes).toEqual(["Applied: Hangzhou"])
    expect(calls[0].data).toMatchObject({ custom_requirement: "Prefer Hangzhou" })
  })

  it("maps the match report and forwards the supplementary resume requirement", async () => {
    const result = await reviewResumeText(
      "Built SQL reports.",
      "2",
      "Data Engineer",
      "Focus on entry-level roles",
    )

    expect(result.jobMatchReport.score).toBe(60)
    expect(result.jobMatchReport.priorityGaps[0].skillName).toBe("Python")
    expect(result.customRequirementNotes).toEqual(["Applied: Entry-level"])
    expect(calls[0].data).toMatchObject({
      custom_requirement: "Focus on entry-level roles",
    })
  })
})
