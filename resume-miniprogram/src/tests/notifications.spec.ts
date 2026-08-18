import { beforeEach, describe, expect, it } from "vitest"

import { notify } from "../utils/notifications"

const notifications: Array<{ title: string; icon?: string }> = []

beforeEach(() => {
  notifications.length = 0
  ;(globalThis as typeof globalThis & { uni: Record<string, unknown> }).uni = {
    showToast: (payload: { title: string; icon?: string }) => notifications.push(payload),
  }
})

describe("notify", () => {
  it("maps success feedback to the shared toast API", () => {
    notify.success("Saved")

    expect(notifications).toEqual([{ title: "Saved", icon: "success" }])
  })

  it("uses a non-blocking toast for errors", () => {
    notify.error("Export failed")

    expect(notifications).toEqual([{ title: "Export failed", icon: "none" }])
  })
})
