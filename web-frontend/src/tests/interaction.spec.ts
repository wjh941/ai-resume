import { describe, expect, it } from "vitest"
import { readFileSync } from "node:fs"

import { useAsyncAction } from "../composables/useAsyncAction"

describe("useAsyncAction", () => {
  it("keeps the future capability shell presentation-only", () => {
    const source = readFileSync(new URL("../components/FutureCapabilityShell.vue", import.meta.url), "utf8")
    expect(source).not.toContain("requestApi")
    expect(source).not.toContain("fetch(")
  })

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

  it("locks career task controls while a task update is pending", () => {
    const source = readFileSync(new URL("../views/CareerView.vue", import.meta.url), "utf8")
    expect(source).toContain("if (pendingTaskId.value) return")
    expect(source).toContain(':loading="pendingTaskId === task.id" :disabled="Boolean(pendingTaskId)"')
  })

  it("locks application follow-up controls while one request is pending", () => {
    const source = readFileSync(new URL("../views/ApplicationsView.vue", import.meta.url), "utf8")
    expect(source).toContain(':loading="pendingKey === `timeline-load:${item.id}`" :disabled="Boolean(pendingKey)"')
    expect(source).toContain(':loading="pendingKey === `timeline-add:${item.id}`" :disabled="Boolean(pendingKey)"')
    expect(source).toContain(':loading="pendingKey === `reminder:${item.id}`" :disabled="Boolean(pendingKey)"')
  })

  it("guards account actions and mode switches while requests are pending", () => {
    const account = readFileSync(new URL("../views/AccountView.vue", import.meta.url), "utf8")
    const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
    const insights = readFileSync(new URL("../views/InsightsView.vue", import.meta.url), "utf8")
    const assessment = readFileSync(new URL("../views/AssessmentView.vue", import.meta.url), "utf8")
    expect(account).toContain("if (pendingAction.value) return")
    expect(account).toContain(':disabled="Boolean(pendingAction)"')
    expect(jobs).toContain(':disabled="loading"')
    expect(insights).toContain(':disabled="loading"')
    expect(assessment).toContain(':disabled="saving"')
  })
})
