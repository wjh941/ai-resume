import { afterEach, describe, expect, it, vi } from "vitest"

import { createDebouncedTask } from "../utils/debounced-task"

afterEach(() => vi.useRealTimers())

describe("createDebouncedTask", () => {
  it("coalesces rapid schedules and runs once after 800ms", () => {
    vi.useFakeTimers()
    const action = vi.fn()
    const task = createDebouncedTask(action, 800)

    task.schedule()
    vi.advanceTimersByTime(500)
    task.schedule()
    vi.advanceTimersByTime(799)
    expect(action).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(action).toHaveBeenCalledTimes(1)
    expect(task.isPending()).toBe(false)
  })

  it("flushes the latest pending action exactly once", () => {
    vi.useFakeTimers()
    const action = vi.fn()
    const task = createDebouncedTask(action, 800)
    task.schedule()
    task.flush()
    vi.runAllTimers()
    expect(action).toHaveBeenCalledTimes(1)
  })

  it("cancels without running", () => {
    vi.useFakeTimers()
    const action = vi.fn()
    const task = createDebouncedTask(action, 800)
    task.schedule()
    task.cancel()
    vi.runAllTimers()
    expect(action).not.toHaveBeenCalled()
  })
})
