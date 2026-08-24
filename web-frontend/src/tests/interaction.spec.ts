import { describe, expect, it } from "vitest"

import { useAsyncAction } from "../composables/useAsyncAction"

describe("useAsyncAction", () => {
  it("clears pending after a successful operation", async () => {
    const action = useAsyncAction()
    const result = await action.run(async () => "saved")

    expect(result).toBe("saved")
    expect(action.pending.value).toBe(false)
  })

  it("clears pending and rethrows after a failed operation", async () => {
    const action = useAsyncAction()
    const failure = Promise.resolve().then(() => action.run(async () => { throw new Error("network") }))

    await expect(failure).rejects.toThrow("network")
    expect(action.pending.value).toBe(false)
  })

  it("ignores a duplicate operation while pending", async () => {
    const action = useAsyncAction()
    let resolve!: (value: string) => void
    const first = action.run(() => new Promise<string>((done) => { resolve = done }))
    const second = await action.run(async () => "duplicate")

    expect(second).toBeUndefined()
    resolve("first")
    await expect(first).resolves.toBe("first")
  })
})
