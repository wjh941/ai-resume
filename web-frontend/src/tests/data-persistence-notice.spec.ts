import { describe, expect, it } from "vitest"

import {
  markPersistenceNoticeDismissed,
  PERSISTENCE_NOTICE_INTERVAL_MS,
  PERSISTENCE_NOTICE_KEY,
  shouldShowPersistenceNotice,
} from "../lib/data-persistence-notice"

function memoryStorage(initial: Record<string, string> = {}) {
  const map = new Map(Object.entries(initial))
  return {
    getItem: (key: string) => map.get(key) ?? null,
    setItem: (key: string, value: string) => { map.set(key, value) },
  }
}

describe("data persistence notice", () => {
  it("shows when never dismissed", () => {
    expect(shouldShowPersistenceNotice(memoryStorage())).toBe(true)
  })

  it("stays hidden within the quiet window and returns after 7 days", () => {
    const now = new Date("2026-03-10T08:00:00Z")
    const storage = memoryStorage()
    markPersistenceNoticeDismissed(storage, now)
    expect(storage.getItem(PERSISTENCE_NOTICE_KEY)).toBe(String(now.getTime()))
    expect(shouldShowPersistenceNotice(storage, new Date(now.getTime() + PERSISTENCE_NOTICE_INTERVAL_MS - 1))).toBe(false)
    expect(shouldShowPersistenceNotice(storage, new Date(now.getTime() + PERSISTENCE_NOTICE_INTERVAL_MS))).toBe(true)
  })

  it("shows again when the stored value is corrupted or storage throws", () => {
    expect(shouldShowPersistenceNotice(memoryStorage({ [PERSISTENCE_NOTICE_KEY]: "not-a-number" }))).toBe(true)
    const throwing = { getItem: () => { throw new Error("blocked") }, setItem: () => undefined }
    expect(shouldShowPersistenceNotice(throwing)).toBe(true)
  })

  it("survives a failing storage on dismiss", () => {
    const throwing = { getItem: () => null, setItem: () => { throw new Error("quota") } }
    expect(() => markPersistenceNoticeDismissed(throwing)).not.toThrow()
  })
})
