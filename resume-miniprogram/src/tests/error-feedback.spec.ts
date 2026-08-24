import { afterEach, describe, expect, it, vi } from "vitest"

import { showErrorToast } from "../utils/error-feedback"

afterEach(() => vi.unstubAllGlobals())

describe("showErrorToast", () => {
  it("uses the shared transient error presentation", () => {
    const showToast = vi.fn()
    vi.stubGlobal("uni", { showToast })

    showErrorToast("network request failed")

    expect(showToast).toHaveBeenCalledWith({
      title: "network request failed",
      icon: "none",
      duration: 2600,
      mask: false,
    })
  })
})
