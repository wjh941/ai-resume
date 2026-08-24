import { describe, expect, it } from "vitest"

import { runWithLoading } from "../utils/async-state"

describe("runWithLoading", () => {
  it("clears loading after resolve", async () => {
    const states: boolean[] = []
    await expect(runWithLoading((value) => states.push(value), async () => "ok")).resolves.toBe("ok")
    expect(states).toEqual([true, false])
  })

  it("clears loading after rejection", async () => {
    const states: boolean[] = []
    await expect(runWithLoading((value) => states.push(value), async () => { throw new Error("offline") }))
      .rejects.toThrow("offline")
    expect(states).toEqual([true, false])
  })

  it("clears loading after an abort-shaped rejection", async () => {
    const states: boolean[] = []
    await expect(runWithLoading((value) => states.push(value), async () => {
      throw new DOMException("The operation was aborted", "AbortError")
    })).rejects.toMatchObject({ name: "AbortError" })
    expect(states).toEqual([true, false])
  })
})
