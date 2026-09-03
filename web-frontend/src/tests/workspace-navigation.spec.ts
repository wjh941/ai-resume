import { readFileSync } from "node:fs"
import { describe, expect, it } from "vitest"

const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")

describe("workspace navigation continuity", () => {
  it("hydrates workspace state from the URL and handles browser history", () => {
    expect(app).toContain('from "./lib/workspace-route"')
    expect(app).toContain("parseWorkspaceRoute")
    expect(app).toContain("history.pushState")
    expect(app).toContain("handlePopState")
    expect(app).toContain("window.addEventListener(\"popstate\", handlePopState)")
    expect(app).toContain("<KeepAlive")
    expect(app).toContain(":key=\"activeView\"")
  })

  it("updates document titles for the active route", () => {
    expect(app).toContain("getWorkspacePageTitle")
    expect(app).toContain("document.title")
  })
})
