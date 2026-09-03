import { readFileSync } from "node:fs"
import { describe, expect, it } from "vitest"

const account = readFileSync(new URL("../views/AccountView.vue", import.meta.url), "utf8")
const comparison = readFileSync(new URL("../views/ComparisonView.vue", import.meta.url), "utf8")
const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
const login = readFileSync(new URL("../components/LoginPanel.vue", import.meta.url), "utf8")

describe("Web retention copy and actions", () => {
  it("keeps account export actionable in the Web workspace", () => {
    expect(account).toContain("downloadApi")
    expect(account).toContain("triggerBlobDownload")
    expect(account).not.toContain("小程序账户中心")
  })

  it("routes missing career data to the Web career planner", () => {
    expect(comparison).toContain("emit('navigate', 'career')")
    expect(comparison).not.toContain("小程序的职业规划")
  })

  it("explains why the login panel appears after session expiry", () => {
    expect(app).toContain(":session-notice=\"sessionExpired ?")
    expect(login).toContain("sessionNotice")
  })

  it("closes the local session immediately after account deletion", () => {
    expect(account).toContain('emit("deleted")')
    expect(app).toContain('@deleted="handleAccountDeleted"')
    expect(app).toContain("clearSession()")
    expect(app).toContain("accountDeletedNotice")
  })

  it("keeps account scope loading recoverable", () => {
    expect(account).toContain("RefreshCw")
    expect(account).toContain('@click="refresh"')
  })
})
