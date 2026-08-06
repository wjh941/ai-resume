import { describe, expect, it } from "vitest"

import { createEmptyResume } from "../types/resume"
import { validateResume } from "../utils/validators"

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
})
