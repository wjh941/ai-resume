// @vitest-environment jsdom

import { describe, expect, it, vi } from "vitest"

import { computeRewriteDiff, type RewriteMode, aiRewriteResume } from "../lib/rewrite"
import type { ResumePayload } from "../lib/drafts"
import { existsSync, readFileSync } from "node:fs"
import { resolve } from "node:path"

vi.mock("../lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../lib/api")>()
  return {
    ...actual,
    requestApi: vi.fn(),
  }
})

const { requestApi } = await import("../lib/api")
const requestApiMock = vi.mocked(requestApi)

function resume(overrides: Partial<ResumePayload> = {}): ResumePayload {
  return {
    version: 1,
    basic: { name: "张三", phone: "13800138000", email: "z@e.com", city: "上海" },
    job: { targetRole: "数据分析师", expectedSalary: "", employmentType: "" },
    education: [],
    employment: [{ company: "示例科技", position: "数据分析", startDate: "2024-01", endDate: "2024-06", description: "搭建看板" }],
    projects: [{ name: "漏斗分析", role: "负责人", startDate: "2024-03", endDate: "2024-06", description: "分析转化" }],
    skills: { skills: ["SQL"], certificates: [] },
    selfEvaluation: "对数据敏感",
    sectionVisibility: {
      basic: true, job: true, education: true, employment: true,
      projects: true, skills: true, selfEvaluation: true,
    },
    ...overrides,
  }
}

describe("computeRewriteDiff", () => {
  it("lists only entries whose descriptive copy changed", () => {
    const before = resume()
    const after = resume({
      employment: [{ ...before.employment[0], description: "搭建并迭代转化漏斗看板" }],
      selfEvaluation: "对数据高度敏感，习惯用数字说话",
    })
    const diff = computeRewriteDiff(before, after)
    expect(diff).toHaveLength(2)
    expect(diff[0]).toMatchObject({ kind: "employment", title: "示例科技 · 数据分析", before: "搭建看板" })
    expect(diff[1]).toMatchObject({ kind: "self", title: "自我评价" })
  })

  it("returns empty diff when nothing changed", () => {
    expect(computeRewriteDiff(resume(), resume())).toEqual([])
  })
})

describe("aiRewriteResume", () => {
  it("posts snake_case payload with instructions and maps the camelCase result", async () => {
    requestApiMock.mockClear()
    requestApiMock.mockResolvedValueOnce({
      basic: { name: "张三", phone: "13800138000", email: "z@e.com", city: "上海" },
      job: { target_role: "数据分析师", expected_salary: "", employment_type: "" },
      education: [],
      employment: [{ company: "示例科技", position: "数据分析", start_date: "2024-01", end_date: "2024-06", description: "改写后的描述" }],
      projects: [],
      skills: { skills: ["SQL"], certificates: [] },
      self_evaluation: "改写后的自我评价",
      section_visibility: { basic: true, job: true, education: true, employment: true, projects: true, skills: true, self_evaluation: false },
    })

    const result = await aiRewriteResume({
      resume: resume(),
      roleName: "商业分析师",
      mode: "light" as RewriteMode,
      instructions: "突出项目管理经验",
    })

    const [path, init] = requestApiMock.mock.calls[0]
    expect(path).toBe("/api/resume/ai-rewrite")
    const body = JSON.parse((init as { body: string }).body)
    expect(body.mode).toBe("light")
    expect(body.instructions).toBe("突出项目管理经验")
    expect(body.job.role_name).toBe("商业分析师")
    expect(body.resume.job.target_role).toBe("数据分析师")
    expect(body.resume.section_visibility.self_evaluation).toBe(true)
    expect(result.employment[0].description).toBe("改写后的描述")
    expect(result.sectionVisibility.selfEvaluation).toBe(false)
  })

  it("sends null instructions when blank", async () => {
    requestApiMock.mockClear()
    requestApiMock.mockResolvedValueOnce({
      basic: { name: "", phone: "", email: "", city: "" },
      job: { target_role: "", expected_salary: "", employment_type: "" },
    })
    await aiRewriteResume({ resume: resume(), roleName: "", mode: "deep" as RewriteMode, instructions: "   " })
    const body = JSON.parse((requestApiMock.mock.calls[0][1] as { body: string }).body)
    expect(body.instructions).toBeNull()
    expect(body.job.role_name).toBe("数据分析师")
  })

  it("wires the AI rewrite panel into the editor with vip fallback", () => {
    const editorPath = resolve(process.cwd(), "src", "views", "ResumeEditorView.vue")
    expect(existsSync(editorPath)).toBe(true)
    const text = readFileSync(editorPath, "utf8")
    expect(text).toContain("aiRewriteResume")
    expect(text).toContain('caught.code === "vip_required"')
    expect(text).toContain("REWRITE_INSTRUCTIONS_MAX")
    expect(text).toContain("applyRewrite")
  })
})
