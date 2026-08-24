import { describe, expect, it } from "vitest"

import { canCompareRoles, toggleComparisonRole } from "../lib/comparison-workflow"

describe("comparison workflow helpers", () => {
  it("prevents duplicate roles and caps selection at four", () => {
    expect(toggleComparisonRole(["数据分析师"], "数据分析师")).toEqual([])
    expect(toggleComparisonRole(["a", "b", "c", "d"], "e")).toEqual(["a", "b", "c", "d"])
  })

  it("allows comparison only inside the 2-4 role range", () => {
    expect(canCompareRoles(["a"])).toBe(false)
    expect(canCompareRoles(["a", "b"])).toBe(true)
    expect(canCompareRoles(["a", "b", "c", "d", "e"])).toBe(false)
  })
})
