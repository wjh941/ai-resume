import { expect, it } from "vitest"

import { previewContact } from "../utils/resume-preview"

it("shows an explicit placeholder only when resume contact data is missing", () => {
  expect(previewContact("", "手机待补充")).toBe("手机待补充")
  expect(previewContact("13800138000", "手机待补充")).toBe("13800138000")
})
