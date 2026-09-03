import { describe, expect, it } from "vitest"

import {
  buildWorkspaceUrl,
  getWorkspacePageTitle,
  parseWorkspaceRoute,
  type WorkspaceRoute,
} from "../lib/workspace-route"

describe("workspace route", () => {
  it("defaults invalid views and restores an editor draft", () => {
    expect(parseWorkspaceRoute({ search: "" })).toEqual({ view: "overview", draftId: null })
    expect(parseWorkspaceRoute({ search: "?view=unknown" })).toEqual({ view: "overview", draftId: null })
    expect(parseWorkspaceRoute({ search: "?view=jobs&draft=draft-42" })).toEqual({ view: "resume", draftId: "draft-42" })
  })

  it("preserves unrelated params and hash while updating workspace state", () => {
    const base = "https://example.test/workspace?utm_source=mail&view=jobs#resume"
    const editor: WorkspaceRoute = { view: "resume", draftId: "draft-42" }
    expect(buildWorkspaceUrl(editor, base)).toBe("/workspace?utm_source=mail&view=resume&draft=draft-42#resume")
    expect(buildWorkspaceUrl({ view: "resume", draftId: null }, buildWorkspaceUrl(editor, base))).toBe("/workspace?utm_source=mail&view=resume#resume")
  })

  it("uses concise, page-specific titles", () => {
    expect(getWorkspacePageTitle({ view: "overview", draftId: null })).toContain("工作概览")
    expect(getWorkspacePageTitle({ view: "resume", draftId: "draft-42" })).toContain("编辑简历")
  })
})
