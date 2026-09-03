import { describe, expect, it } from "vitest"
import { readFileSync } from "node:fs"
import { validateInsightsQuerySnapshot, validateJobsQuerySnapshot } from "../lib/query-recovery"

const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
const insights = readFileSync(new URL("../views/InsightsView.vue", import.meta.url), "utf8")
const queryRecovery = readFileSync(new URL("../lib/query-recovery.ts", import.meta.url), "utf8")

describe("query continuity", () => {
  it("recovers and persists validated Jobs query inputs", () => {
    expect(jobs).toContain('import { readSession } from "../lib/session"')
    expect(jobs).toContain('readWorkspaceSnapshot<unknown>(workspaceStorage, workspaceUserId, "jobs-query")')
    expect(jobs).toContain('writeWorkspaceSnapshot(workspaceStorage, workspaceUserId, "jobs-query"')
    expect(jobs).toContain("validateJobsQuerySnapshot")
    expect(jobs).toMatch(/roleName\.value\s*=\s*recovered\.roleName/)
    expect(jobs).toMatch(/reportMode\.value\s*=\s*recovered\.reportMode/)
  })

  it("recovers and persists validated Insights query inputs", () => {
    expect(insights).toContain('import { readSession } from "../lib/session"')
    expect(insights).toContain('readWorkspaceSnapshot<unknown>(workspaceStorage, workspaceUserId, "insights-query")')
    expect(insights).toContain('writeWorkspaceSnapshot(workspaceStorage, workspaceUserId, "insights-query"')
    expect(insights).toContain("validateInsightsQuerySnapshot")
    expect(insights).toMatch(/roleName\.value\s*=\s*recovered\.roleName/)
    expect(insights).toMatch(/year\.value\s*=\s*recovered\.year/)
    expect(insights).toMatch(/reportMode\.value\s*=\s*recovered\.reportMode/)
  })

  it("guards sessionStorage access and does not persist API results", () => {
    for (const source of [jobs, insights]) {
      expect(source).toMatch(/try\s*\{\s*return typeof sessionStorage === "undefined" \? null : sessionStorage/s)
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
})
