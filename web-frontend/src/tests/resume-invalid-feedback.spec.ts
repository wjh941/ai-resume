import { describe, expect, it, vi } from "vitest"

import { focusFirstInvalidResumeField, resolveResumeInvalidSummary } from "../lib/resume-invalid-feedback"

describe("focusFirstInvalidResumeField", () => {
  it("focuses and centers the first invalid resume control in form order", () => {
    const focus = vi.fn()
    const scrollIntoView = vi.fn()
    const root = {
      getElementById: vi.fn((id: string) => id === "resume-basic-name" ? { focus, scrollIntoView } : null),
    }

    expect(focusFirstInvalidResumeField({ "basic.name": "required", "basic.email": "invalid" }, root)).toBe(true)
    expect(root.getElementById).toHaveBeenCalledWith("resume-basic-name")
    expect(focus).toHaveBeenCalledWith({ preventScroll: true })
    expect(scrollIntoView).toHaveBeenCalledWith({ block: "center", behavior: "smooth" })
  })

  it("returns false without moving focus when no mapped invalid control exists", () => {
    const root = { getElementById: vi.fn(() => null) }

    expect(focusFirstInvalidResumeField({ unknown: "invalid" }, root)).toBe(false)
    expect(root.getElementById).not.toHaveBeenCalled()
  })
})

describe("resolveResumeInvalidSummary", () => {
  it("stays silent before submit, follows the current first error, and clears after correction", () => {
    const multipleErrors = { "basic.name": "name required", "basic.phone": "phone invalid" }

    expect(resolveResumeInvalidSummary(false, multipleErrors)).toBe("")
    expect(resolveResumeInvalidSummary(true, multipleErrors)).toBe("name required")
    expect(resolveResumeInvalidSummary(true, { "basic.phone": "phone invalid" })).toBe("phone invalid")
    expect(resolveResumeInvalidSummary(true, {})).toBe("")
  })
})
