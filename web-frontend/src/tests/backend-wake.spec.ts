import { describe, expect, it, vi } from "vitest"

import { createBackendWakeMonitor } from "../lib/backend-wake"

function flush(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

describe("backend wake monitor", () => {
  it("clears waking on a healthy probe", async () => {
    const requestFn = vi.fn().mockResolvedValue(true)
    const monitor = createBackendWakeMonitor({ requestFn, autoStop: false })
    expect(monitor.waking.value).toBe(true)
    const ok = await monitor.probe()
    expect(ok).toBe(true)
    expect(monitor.waking.value).toBe(false)
    expect(monitor.attempts.value).toBe(1)
    expect(monitor.lastError.value).toBe("")
  })

  it("retries after failures and surfaces the last error", async () => {
    const requestFn = vi.fn()
      .mockRejectedValueOnce(new Error("请求超时"))
      .mockResolvedValueOnce(true)
    const monitor = createBackendWakeMonitor({ requestFn, intervalMs: 1, autoStop: false })
    const first = await monitor.probe()
    expect(first).toBe(false)
    expect(monitor.waking.value).toBe(true)
    expect(monitor.lastError.value).toBe("请求超时")
    await flush(5)
    expect(requestFn).toHaveBeenCalledTimes(2)
    expect(monitor.waking.value).toBe(false)
  })

  it("stops retrying after max attempts", async () => {
    const requestFn = vi.fn().mockResolvedValue(false)
    const monitor = createBackendWakeMonitor({ requestFn, intervalMs: 1, maxAttempts: 2, autoStop: false })
    await monitor.probe()
    await flush(5)
    await flush(5)
    expect(monitor.attempts.value).toBeLessThanOrEqual(2)
  })
})
