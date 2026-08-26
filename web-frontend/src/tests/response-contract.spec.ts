import { describe, expect, it } from "vitest"

import { ApiRequestError, readItems } from "../lib/api"

describe("readItems", () => {
  it("returns direct arrays unchanged", () => {
    const items = [{ id: 1 }, { id: 2 }]

    expect(readItems(items)).toBe(items)
  })

  it("returns envelope items unchanged", () => {
    const items = [{ id: 1 }, { id: 2 }]

    expect(readItems({ items })).toBe(items)
  })

  it.each([null, undefined, {}, { items: null }])("rejects malformed list payload %j", (payload) => {
    try {
      readItems(payload as never)
      throw new Error("expected readItems to reject the payload")
    } catch (error) {
      expect(error).toBeInstanceOf(ApiRequestError)
      expect(error).toMatchObject({ status: 0 })
    }
  })
})
