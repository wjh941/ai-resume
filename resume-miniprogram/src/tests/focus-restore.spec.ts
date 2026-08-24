import { describe, expect, it, vi } from "vitest"

import { captureFocusRestore } from "../utils/focus-restore"

describe("captureFocusRestore", () => {
  it("is a no-op without an H5 document", () => {
    expect(() => captureFocusRestore(undefined)()).not.toThrow()
  })

  it("restores a still-connected focusable element", () => {
    const focus = vi.fn()
    const restore = captureFocusRestore({ activeElement: { isConnected: true, focus } })
    restore()
    expect(focus).toHaveBeenCalledTimes(1)
  })

  it("does not focus a removed element", () => {
    const focus = vi.fn()
    const restore = captureFocusRestore({ activeElement: { isConnected: false, focus } })
    restore()
    expect(focus).not.toHaveBeenCalled()
  })
})
