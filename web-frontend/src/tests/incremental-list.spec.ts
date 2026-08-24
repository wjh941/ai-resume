import { ref } from "vue"
import { describe, expect, it } from "vitest"

import { useIncrementalList } from "../composables/useIncrementalList"

describe("useIncrementalList for Web", () => {
  it("renders 40 records and advances by 40 without exceeding length", () => {
    const source = ref(Array.from({ length: 95 }, (_, index) => index))
    const list = useIncrementalList(source)

    expect(list.visibleItems.value).toHaveLength(40)
    list.showMore()
    expect(list.visibleItems.value).toHaveLength(80)
    list.showMore()
    expect(list.visibleItems.value).toHaveLength(95)
    expect(list.hasMore.value).toBe(false)
  })

  it("resets after a refresh or filter change", () => {
    const source = ref(Array.from({ length: 95 }, (_, index) => index))
    const list = useIncrementalList(source)

    list.showMore()
    list.reset()

    expect(list.visibleItems.value).toHaveLength(40)
  })

  it("keeps new source records visible without growing beyond its current window", () => {
    const source = ref(Array.from({ length: 95 }, (_, index) => index))
    const list = useIncrementalList(source)

    list.showMore()
    source.value = [999, ...source.value]

    expect(list.visibleItems.value).toHaveLength(80)
    expect(list.visibleItems.value[0]).toBe(999)
  })
})
