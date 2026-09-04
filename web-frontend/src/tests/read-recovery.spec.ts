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
  it("maps page read failures through the shared API error copy", () => {
    for (const source of Object.values(viewSources)) {
      expect(source).toContain('from "../lib/api-error"')
      expect(source).toMatch(/catch \(reason\)[\s\S]{0,260}getApiErrorMessage\(reason,/)
    }
  })

  it("exposes a retry action for each page refresh failure", () => {
    for (const source of Object.values(viewSources)) {
      expect(source).toContain("retryAction")
      expect(source).toContain("retryFailedRequest")
      expect(source).toContain('@click="retryFailedRequest"')
    }
  })

  it("clears the page retry action before mutation failures", () => {
    for (const source of Object.values(viewSources)) {
      expect(source).toContain("retryAction.value = null")
    }
  })
})
