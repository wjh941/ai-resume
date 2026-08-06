import { expect, it } from "vitest"

import { meaningfulEntries, previewContact } from "../utils/resume-preview"

it("shows an explicit placeholder only when resume contact data is missing", () => {
  expect(previewContact("", "手机待补充")).toBe("手机待补充")
  expect(previewContact("13800138000", "手机待补充")).toBe("13800138000")
})

it("filters completely blank factual entries before preview rendering", () => {
  const entries = meaningfulEntries([
    { school: "", major: "", degree: "", startDate: "", endDate: "", courses: "" },
    { school: "清华大学", major: "", degree: "", startDate: "", endDate: "", courses: "" },
  ])

  expect(entries).toEqual([
    { school: "清华大学", major: "", degree: "", startDate: "", endDate: "", courses: "" },
  ])
})
