import { ref } from "vue"
import { describe, expect, it } from "vitest"

import { useIncrementalList } from "../composables/useIncrementalList"

describe("useIncrementalList for H5", () => {
  it("renders 20 records and advances by 20 without exceeding length", () => {
    const source = ref(Array.from({ length: 45 }, (_, index) => index))
    const list = useIncrementalList(source)
    expect(list.visibleItems.value).toHaveLength(20)
    list.showMore()
    expect(list.visibleItems.value).toHaveLength(40)
    list.showMore()
    expect(list.visibleItems.value).toHaveLength(45)
    expect(list.hasMore.value).toBe(false)
  })

  it("resets after a refresh or filter change", () => {
    const source = ref(Array.from({ length: 60 }, (_, index) => index))
    const list = useIncrementalList(source)
    list.showMore()
    list.reset()
    expect(list.visibleItems.value).toHaveLength(20)
  })
})
