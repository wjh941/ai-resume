import { beforeEach, describe, expect, it } from "vitest"
import { createPinia, setActivePinia } from "pinia"

import { useCareerStore } from "../stores/career"

const storage = new Map<string, unknown>()

beforeEach(() => {
  storage.clear()
  setActivePinia(createPinia())
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
  }
})

describe("career comparison state", () => {
  it("limits comparison selection to four unique roles", () => {
    const store = useCareerStore()

    expect(store.toggleComparisonRole("数据工程师")).toBe(true)
    expect(store.toggleComparisonRole("数据工程师")).toBe(true)
    expect(store.comparisonRoleNames).toEqual([])

    for (const role of ["数据工程师", "数据分析师", "数据治理工程师", "机器学习工程师"]) {
      expect(store.toggleComparisonRole(role)).toBe(true)
    }
    expect(store.toggleComparisonRole("产品经理")).toBe(false)
    expect(store.comparisonRoleNames).toHaveLength(4)
  })
})
