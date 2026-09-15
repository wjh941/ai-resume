import { describe, expect, it } from "vitest"
import { readFileSync } from "node:fs"
import { validateInsightsQuerySnapshot, validateJobsQuerySnapshot } from "../lib/query-recovery"

const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
const insights = readFileSync(new URL("../views/InsightsView.vue", import.meta.url), "utf8")
const queryRecovery = readFileSync(new URL("../lib/query-recovery.ts", import.meta.url), "utf8")
const sessionSnapshot = readFileSync(new URL("../lib/session-snapshot.ts", import.meta.url), "utf8")

describe("query continuity", () => {
  it("recovers and persists validated Jobs query inputs", () => {
    expect(jobs).toContain('import { readSession } from "../lib/session"')
    expect(jobs).toContain("readSessionSnapshot<unknown>(jobsQueryKey)")
    expect(jobs).toContain("writeSessionSnapshot(jobsQueryKey")
    expect(jobs).toContain("validateJobsQuerySnapshot")
    expect(jobs).toMatch(/roleName\.value\s*=\s*recovered\.roleName/)
    expect(jobs).toMatch(/reportMode\.value\s*=\s*recovered\.reportMode/)
  })

  it("recovers and persists validated Insights query inputs", () => {
    expect(insights).toContain('import { readSession } from "../lib/session"')
    expect(insights).toContain("readSessionSnapshot<unknown>(insightsQueryKey)")
    expect(insights).toContain("writeSessionSnapshot(insightsQueryKey")
    expect(insights).toContain("validateInsightsQuerySnapshot")
    expect(insights).toMatch(/roleName\.value\s*=\s*recovered\.roleName/)
    expect(insights).toMatch(/year\.value\s*=\s*recovered\.year/)
    expect(insights).toMatch(/reportMode\.value\s*=\s*recovered\.reportMode/)
  })

  it("guards sessionStorage access in one shared helper and does not persist API results", () => {
    expect(sessionSnapshot).toMatch(/try\s*\{\s*return typeof sessionStorage === "undefined" \? null : sessionStorage/s)
    expect(sessionSnapshot).toMatch(/catch\s*\{\s*return null\s*\}/s)
    for (const source of [jobs, insights]) {
      expect(source).not.toContain("workspaceStorage")
      expect(source).not.toMatch(/watch\(result/)
      expect(source).not.toMatch(/watch\(report/)
    }
  })

  it("validates mode and year before restoring snapshots", () => {
    expect(queryRecovery).toMatch(/value === "simplified" \|\| value === "professional"/)
    expect(queryRecovery).toContain('typeof candidate.year === "string" && /^\\d{4}$/.test(candidate.year)')
    expect(queryRecovery).toMatch(/Number\(candidate\.year\) >= 2000 && Number\(candidate\.year\) <= 2100/)
  })

  it("drops invalid query fields at runtime", () => {
    expect(validateJobsQuerySnapshot({ roleName: 42, reportMode: "unknown" })).toEqual({})
    expect(validateInsightsQuerySnapshot({ roleName: "analyst", year: "1999", reportMode: "unknown" })).toEqual({ roleName: "analyst" })
  })

  it("maps query failures through the shared resource fallback and keeps retry available", () => {
    expect(jobs).toContain('fallbackMessage: "岗位分析暂时不可用。请确认 AI 服务已配置，或稍后重试。"')
    expect(insights).toContain('fallbackMessage: "年度洞察暂时无法查询。请检查权限或稍后重试。"')
    // JobsView 的收藏动作仍直接复用共享 API 错误文案映射。
    expect(jobs).toContain('getApiErrorMessage(reason, "岗位收藏未保存，请稍后重试")')
    for (const source of [jobs, insights]) {
      expect(source).toContain('v-if="retryable"')
      expect(source).toContain('@click="retryFailedRequest"')
    }
  })
})
