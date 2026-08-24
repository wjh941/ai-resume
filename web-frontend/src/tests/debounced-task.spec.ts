import { afterEach, describe, expect, it, vi } from "vitest"

import { createDebouncedTask } from "../lib/debounced-task"

afterEach(() => vi.useRealTimers())

describe("createDebouncedTask for Web", () => {
  it("coalesces rapid schedules into one 800ms action", () => {
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
  })

  it("flushes once and cancels the timer", () => {
    vi.useFakeTimers()
    const action = vi.fn()
    const task = createDebouncedTask(action, 800)
    task.schedule()
    task.flush()
    vi.runAllTimers()
    expect(action).toHaveBeenCalledTimes(1)
    expect(task.isPending()).toBe(false)
  })

  it("cancels without running", () => {
    vi.useFakeTimers()
    const action = vi.fn()
    const task = createDebouncedTask(action, 800)
    task.schedule()
    task.cancel()
    vi.runAllTimers()
    expect(action).not.toHaveBeenCalled()
    expect(task.isPending()).toBe(false)
  })
})
