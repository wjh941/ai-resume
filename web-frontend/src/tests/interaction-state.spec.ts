import { describe, expect, it } from "vitest"

import { canStartInteraction, pendingLabel } from "../lib/interaction-state"

describe("interaction state helpers", () => {
  it("blocks duplicate interactions while loading", () => {
    expect(canStartInteraction(true)).toBe(false)
    expect(canStartInteraction(false)).toBe(true)
  })

  it("selects the pending label without changing idle copy", () => {
    expect(pendingLabel(true, "保存", "保存中")).toBe("保存中")
    expect(pendingLabel(false, "保存", "保存中")).toBe("保存")
  })
})
