import { describe, expect, it, vi } from "vitest"

import { createResumeInvalidFeedback, focusFirstInvalidResumeField } from "../lib/resume-invalid-feedback"

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

describe("createResumeInvalidFeedback", () => {
  it("owns activation, error synchronization, clearing, and reset semantics", () => {
    const feedback = createResumeInvalidFeedback()
    const multipleErrors = { "basic.name": "name required", "basic.phone": "phone invalid" }

    feedback.sync(multipleErrors)
    expect(feedback.summary.value).toBe("")

    feedback.activate(multipleErrors)
    expect(feedback.summary.value).toBe("name required")
    feedback.sync({ "basic.phone": "phone invalid" })
    expect(feedback.summary.value).toBe("phone invalid")
    feedback.sync({})
    expect(feedback.summary.value).toBe("")

    feedback.sync(multipleErrors)
    expect(feedback.summary.value).toBe("name required")
    feedback.reset()
    feedback.sync(multipleErrors)
    expect(feedback.summary.value).toBe("")
  })
})
