import { readFileSync } from "node:fs"
import { describe, expect, it } from "vitest"

const account = readFileSync(new URL("../views/AccountView.vue", import.meta.url), "utf8")
const comparison = readFileSync(new URL("../views/ComparisonView.vue", import.meta.url), "utf8")

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
})
