import { beforeEach, describe, expect, it } from "vitest"

import { completeOnboarding, hasCompletedOnboarding } from "../utils/onboarding"

const storage = new Map<string, unknown>()

beforeEach(() => {
  storage.clear()
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
  }
})

describe("first-login onboarding", () => {
  it("shows until the current user completes the guide", () => {
    expect(hasCompletedOnboarding("user-1")).toBe(false)

    completeOnboarding("user-1")

    expect(hasCompletedOnboarding("user-1")).toBe(true)
  })

  it("keeps each user's onboarding state separate", () => {
    completeOnboarding("user-1")

    expect(hasCompletedOnboarding("user-1")).toBe(true)
    expect(hasCompletedOnboarding("user-2")).toBe(false)
  })
})
