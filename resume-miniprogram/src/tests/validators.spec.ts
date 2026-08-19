import { describe, expect, it } from "vitest"

import { createEmptyResume } from "../types/resume"
import { toValidationErrorMap, validateResume } from "../utils/validators"

describe("validateResume", () => {
  it("rejects invalid phone", () => {
    const resume = createEmptyResume()
    resume.basic.name = "张三"
    resume.basic.phone = "123"
    resume.basic.email = "zhang@example.com"
    resume.job.targetRole = "数据工程师"

    expect(validateResume(resume)).toContainEqual(
      expect.objectContaining({ field: "basic.phone" }),
    )
  })

  it("maps validation messages to their matching form fields", () => {
    expect(toValidationErrorMap([
      { field: "basic.phone", message: "Enter a valid phone number" },
    ])).toEqual({ "basic.phone": "Enter a valid phone number" })
  })
})
