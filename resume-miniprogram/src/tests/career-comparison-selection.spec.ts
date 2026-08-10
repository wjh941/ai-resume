import { describe, expect, it } from "vitest"

import { canOpenComparison } from "../utils/role-comparison"

describe("role comparison selection", () => {
  it("requires two to four roles before opening a comparison", () => {
    expect(canOpenComparison([])).toBe(false)
    expect(canOpenComparison(["数据工程师"])).toBe(false)
    expect(canOpenComparison(["数据工程师", "数据分析师"])).toBe(true)
    expect(canOpenComparison(["数据工程师", "数据分析师", "数据治理工程师", "机器学习工程师"])).toBe(true)
    expect(canOpenComparison(["a", "b", "c", "d", "e"])).toBe(false)
  })
})
