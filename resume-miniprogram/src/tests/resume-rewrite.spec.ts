// @vitest-environment node

import { beforeEach, describe, expect, it, vi } from "vitest"

const requestMock = vi.fn()

vi.mock("../services/http", () => ({
  request: (...args: unknown[]) => requestMock(...args),
  apiUrl: (path: string) => path,
  toUserMessage: (reason: unknown, fallback: string) => (reason instanceof Error ? reason.message : fallback),
}))

vi.mock("../stores/session", () => ({
  getAuthToken: () => null,
  getClientId: () => "test-client",
}))

import { aiRewriteResume } from "../services/resume-api"
import type { ResumePayload } from "../types/resume"

function baseResume(): ResumePayload {
  return {
    version: 1,
    basic: { name: "张三", phone: "13800138000", email: "z@e.com", city: "上海", gender: "男" },
    job: { targetRole: "数据分析师", availability: "全职", expectedSalary: "" },
    education: [],
    employment: [{ company: "示例科技", position: "数据分析", startDate: "2024-01", endDate: "2024-06", description: "搭建看板" }],
    projects: [],
    skills: { skills: ["SQL"], certificates: [], englishLevel: "CET-6" },
    selfEvaluation: "对数据敏感",
    sectionVisibility: {
      basic: true, job: true, education: true, employment: true,
      projects: true, skills: true, selfEvaluation: true,
    },
  }
}

describe("aiRewriteResume", () => {
  beforeEach(() => {
    requestMock.mockReset()
  })

  it("posts snake_case payload with trimmed instructions and maps camelCase result", async () => {
    requestMock.mockResolvedValueOnce({
      basic: { name: "张三", phone: "13800138000", email: "z@e.com", city: "上海", gender: "男" },
      job: { target_role: "数据分析师", employment_type: "全职", expected_salary: "" },
      education: [],
      employment: [{ company: "示例科技", position: "数据分析", start_date: "2024-01", end_date: "2024-06", description: "改写后" }],
      projects: [],
      skills: { skills: ["SQL"], certificates: [], englishLevel: "CET-6" },
      self_evaluation: "改写后的自我评价",
      section_visibility: { basic: true, job: true, education: true, employment: true, projects: true, skills: true, self_evaluation: false },
    })

    const result = await aiRewriteResume(baseResume(), " 商业分析师 ", "light", "  突出项目管理经验  ")

    const [path, method, body] = requestMock.mock.calls[0]
    expect(path).toBe("/api/resume/ai-rewrite")
    expect(method).toBe("POST")
    expect(body.mode).toBe("light")
    expect(body.instructions).toBe("突出项目管理经验")
    expect(body.job.role_name).toBe("商业分析师")
    expect(body.resume.job.target_role).toBe("数据分析师")
    expect(body.resume.employment[0].description).toBe("搭建看板")
    expect(result.employment[0].description).toBe("改写后")
    expect(result.sectionVisibility.selfEvaluation).toBe(false)
  })

  it("sends null instructions when blank and falls back to resume role", async () => {
    requestMock.mockResolvedValueOnce({
      basic: { name: "", phone: "", email: "", city: "" },
      job: { target_role: "", employment_type: "", expected_salary: "" },
    })
    await aiRewriteResume(baseResume(), "", "deep", "   ")
    const body = requestMock.mock.calls[0][2] as Record<string, unknown>
    expect(body.instructions).toBeNull()
    expect((body.job as Record<string, unknown>).role_name).toBe("数据分析师")
    expect(body.mode).toBe("deep")
  })
})
