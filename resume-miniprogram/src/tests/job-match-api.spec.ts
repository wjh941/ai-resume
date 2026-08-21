import { beforeEach, describe, expect, it } from "vitest"

import { listLocalJobMatches } from "../services/job-match-api"

const calls: Array<Record<string, unknown>> = []

beforeEach(() => {
  calls.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: () => "token",
    request: async (options: Record<string, unknown>) => {
      calls.push(options)
      return {
        statusCode: 200,
        data: {
          code: "ok",
          message: "",
          data: {
            items: [{
              role_name: "数据分析师",
              company: "澄明数据科技（模拟）",
              city: "上海",
              salary_range: "12k-18k（模拟参考）",
              seniority: "mid",
              category: "数据与数据平台",
              match_score: 78,
              matched_skills: ["SQL"],
              missing_skills: ["Python"],
              description: "本地模拟岗位参考。",
              responsibilities: ["维护业务指标体系"],
              requirements: ["SQL", "Python"],
              detail_unlocked: true,
            }],
            total: 1,
            limited: false,
            source_notice: "本地参考",
          },
        },
      }
    },
  }
})

describe("local job match API", () => {
  it("posts the selected target role and maps local responsibilities", async () => {
    const result = await listLocalJobMatches("数据分析师")

    expect(calls[0]).toMatchObject({
      url: "/api/job/match",
      method: "POST",
      data: { target_role: "数据分析师" },
    })
    expect(result.items[0]).toMatchObject({
      roleName: "数据分析师",
      company: "澄明数据科技（模拟）",
      responsibilities: ["维护业务指标体系"],
    })
  })
})
