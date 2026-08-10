import { beforeEach, describe, expect, it } from "vitest"

import { compareRoles } from "../services/career-api"

const calls: Array<{ url: string; data?: unknown }> = []

beforeEach(() => {
  calls.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async (options: Record<string, unknown>) => {
      calls.push({ url: String(options.url), data: options.data })
      return {
        statusCode: 200,
        data: {
          code: "ok",
          data: {
            profile: {
              client_id: "client-a",
              identity_code: "2",
              major: "计算机科学与技术",
              education_level: "本科",
              graduation_year: 2027,
              city_preferences: [],
              minimum_salary: null,
              industry_preferences: [],
              work_types: ["全职"],
              skills: ["Python"],
              draft_id: null,
              updated_at: "2026-08-10T00:00:00+00:00",
            },
            items: [{
              role: {
                role_name: "数据工程师",
                family: "数据与数据平台",
                aliases: ["data engineer"],
                recommended_majors: ["计算机科学与技术"],
                adjacent_majors: [],
                relevant_courses: [],
                required_skills: ["Python", "SQL"],
                entry_skills: ["Python"],
                alternative_roles: ["ETL工程师"],
                internship_roles: ["数据开发实习生"],
                entry_difficulty: 4,
                industry_tags: ["互联网"],
                description: "Build data pipelines.",
              },
              total_score: 72,
              matching_level: "transferable",
              score_breakdown: [],
              matching_advantages: ["专业与岗位方向直接关联。"],
              missing_skills: ["SQL"],
              alternatives: ["ETL工程师"],
              risk_notice: "不代表录用概率。",
              action_plan: {
                seven_day: ["Python practice"],
                thirty_day: ["Project"],
                ninety_day: ["Apply"],
              },
            }],
            common_strengths: ["专业与岗位方向直接关联。"],
            recommendation_notice: "不代表录用概率。",
          },
        },
      }
    },
  }
})

describe("career comparison API mapping", () => {
  it("maps three action-plan phases from the local comparison response", async () => {
    const result = await compareRoles("client-a", ["数据工程师", "数据分析师"])

    expect(result.items[0].actionPlan.sevenDay).toEqual(["Python practice"])
    expect(result.items[0].riskNotice).toContain("不代表录用")
    expect(calls[0].url).toContain("/api/career/compare")
    expect(calls[0].data).toEqual({
      client_id: "client-a",
      role_names: ["数据工程师", "数据分析师"],
    })
  })
})
