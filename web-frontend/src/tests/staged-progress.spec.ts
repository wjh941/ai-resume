// @vitest-environment jsdom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { createStagedProgress } from "../composables/staged-progress"

describe("staged progress", () => {
  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it("advances through stages and counts elapsed seconds", () => {
    const progress = createStagedProgress(["一", "二", "三"], 10_000)
    progress.start()
    expect(progress.active.value).toBe(true)
    expect(progress.label.value).toBe("一")
    expect(progress.elapsedSeconds.value).toBe(0)
    vi.advanceTimersByTime(10_000)
    expect(progress.label.value).toBe("二")
    expect(progress.elapsedSeconds.value).toBe(10)
    vi.advanceTimersByTime(10_000)
    expect(progress.label.value).toBe("三")
    vi.advanceTimersByTime(30_000)
    expect(progress.label.value).toBe("三")
    expect(progress.elapsedSeconds.value).toBe(50)
  })

  it("restarts cleanly and stops timers", () => {
    const progress = createStagedProgress(["一", "二"], 5_000)
    progress.start()
    vi.advanceTimersByTime(6_000)
    progress.start()
    expect(progress.label.value).toBe("一")
    expect(progress.elapsedSeconds.value).toBe(0)
    progress.stop()
    expect(progress.active.value).toBe(false)
    vi.advanceTimersByTime(20_000)
    expect(progress.elapsedSeconds.value).toBe(0)
  })

  it("keeps a single stage static when only one is provided", () => {
    const progress = createStagedProgress(["只此一段"], 1_000)
    progress.start()
    vi.advanceTimersByTime(5_000)
    expect(progress.label.value).toBe("只此一段")
    expect(progress.elapsedSeconds.value).toBe(5)
  })
})
