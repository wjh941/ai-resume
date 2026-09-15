import { describe, expect, it } from "vitest"
import { readFileSync } from "node:fs"

const viewSources = {
  overview: readFileSync(new URL("../views/OverviewView.vue", import.meta.url), "utf8"),
  resume: readFileSync(new URL("../views/ResumeView.vue", import.meta.url), "utf8"),
  career: readFileSync(new URL("../views/CareerView.vue", import.meta.url), "utf8"),
  evidence: readFileSync(new URL("../views/EvidenceView.vue", import.meta.url), "utf8"),
  applications: readFileSync(new URL("../views/ApplicationsView.vue", import.meta.url), "utf8"),
  membership: readFileSync(new URL("../views/MembershipView.vue", import.meta.url), "utf8"),
  account: readFileSync(new URL("../views/AccountView.vue", import.meta.url), "utf8"),
}

describe("read recovery", () => {
  it("loads every page through the shared useApiResource with a per-view fallback copy", () => {
    for (const source of Object.values(viewSources)) {
      expect(source).toContain("useApiResource")
      expect(source).toMatch(/fallbackMessage: "/)
    }
  })

  it("maps in-page action failures through the shared API error copy", () => {
    for (const [view, source] of Object.entries(viewSources)) {
      // 概览页只有页面级读取，其失败映射由 useApiResource + 兜底文案承担。
      if (view === "overview") continue
      expect(source).toContain('from "../lib/api-error"')
      expect(source).toMatch(/catch \((?:reason|caught)\)[\s\S]{0,260}getApiErrorMessage\((?:reason|caught),/)
    }
  })

  it("exposes a retry action for each page refresh failure", () => {
    for (const source of Object.values(viewSources)) {
      expect(source).toContain('v-if="retryable"')
      expect(source).toContain('@click="retryFailedRequest"')
    }
  })

  it("clears the page retry state before mutation actions", () => {
    for (const [view, source] of Object.entries(viewSources)) {
      // 概览页没有会覆盖页面错误的次级操作。
      if (view === "overview") continue
      expect(source).toContain("clearRetry()")
    }
  })

  it("clears the page retry state before creating a resume", () => {
    const createStart = viewSources.resume.indexOf("async function create()")
    const createBody = viewSources.resume.slice(createStart, viewSources.resume.indexOf("async function copy", createStart))
    expect(createBody).toContain("clearRetry()")
  })
})
