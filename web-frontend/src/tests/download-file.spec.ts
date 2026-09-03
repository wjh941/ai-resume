// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest"

import { triggerBlobDownload } from "../lib/download-file"

describe("triggerBlobDownload", () => {
  afterEach(() => vi.restoreAllMocks())

  it("creates a temporary download link and releases its object URL", () => {
    const blob = new Blob(["account-data"], { type: "application/zip" })
    const createObjectURL = vi.fn(() => "blob:account-data")
    const revokeObjectURL = vi.fn()
    Object.defineProperty(URL, "createObjectURL", { configurable: true, value: createObjectURL })
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: revokeObjectURL })
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function () {
      expect(this.download).toBe("account.zip")
      expect(this.href).toContain("blob:account-data")
    })

    triggerBlobDownload(blob, "account.zip")

    expect(createObjectURL).toHaveBeenCalledWith(blob)
    expect(click).toHaveBeenCalledOnce()
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:account-data")
  })
})
