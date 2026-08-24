import { describe, expect, it } from "vitest"

import { prependDraft, removeDraftById } from "../lib/draft-workflow"

describe("draft workflow helpers", () => {
  it("removes only the confirmed draft", () => {
    expect(removeDraftById([{ id: "d-1" }, { id: "d-2" }], "d-1"))
      .toEqual([{ id: "d-2" }])
  })

  it("prepends a copied draft without mutating the existing list", () => {
    const drafts = [{ id: "d-1" }]
    const copied = { id: "d-2" }

    expect(prependDraft(drafts, copied)).toEqual([copied, drafts[0]])
    expect(drafts).toEqual([{ id: "d-1" }])
  })
})
