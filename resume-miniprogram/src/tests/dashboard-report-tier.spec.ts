import { describe, expect, it } from "vitest"
import { readFileSync } from "node:fs"
import { resolve } from "node:path"
import {
  normalizeReport,
  visibleEvidence,
  withReportMode,
} from "../../public/dashboard-report-tier.js"

describe("dashboard report tier delivery", () => {
  it("adds only valid report modes to API payloads", () => {
    expect(withReportMode({ role_name: "Data Engineer" }, "professional")).toEqual({
      role_name: "Data Engineer",
      report_mode: "professional",
    })
    expect(withReportMode({ role_name: "Data Engineer" }, "auto")).toEqual({
      role_name: "Data Engineer",
    })
  })

  it("never exposes professional evidence from a simplified report", () => {
    const report = normalizeReport({
      report: { mode: "simplified", summary: "Improve SQL", actions: ["Practice joins"], evidence: [{ title: "hidden" }] },
    })
    expect(visibleEvidence(report)).toEqual([])
  })

  it("ships the standalone dashboard through Vite public assets", () => {
    const html = readFileSync(resolve(process.cwd(), "public/premium-dashboard.html"), "utf8")
    expect(html).toContain('src="./dashboard-report-tier.js"')
  })

  it("includes an accessible annual-insight query with layered report output", () => {
    const html = readFileSync(resolve(process.cwd(), "public/premium-dashboard.html"), "utf8")
    expect(html).toContain('id="annualInsightQueryForm"')
    expect(html).toContain('id="annualInsightRole"')
    expect(html).toContain('id="annualInsightYear"')
    expect(html).toContain('id="annualInsightResult"')
    expect(html).toContain("function requestAnnualInsight")
    expect(html).toContain("function renderLayeredReport")
    expect(html).toContain("/api/career/annual-insights/query")
  })

  it("sends the selected report tier with connected analysis requests", () => {
    const html = readFileSync(resolve(process.cwd(), "public/premium-dashboard.html"), "utf8")
    expect(html).toContain("withCurrentReportMode")
    expect(html).toContain("report_mode")
    expect(html).toContain("report: plan?.report || null")
  })
})
