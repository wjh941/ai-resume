import { beforeEach, describe, expect, it } from "vitest"
import { createPinia, setActivePinia } from "pinia"

import { getClientId } from "../stores/session"
import { useResumeStore } from "../stores/resume"

const storage = new Map<string, unknown>()

beforeEach(() => {
  storage.clear()
  setActivePinia(createPinia())
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
  }
})

describe("local client and resume checkpoint", () => {
  it("keeps one generated client id", () => {
    expect(getClientId()).toBe(getClientId())
  })

  it("restores a meaningful local checkpoint", () => {
    const store = useResumeStore()
    store.draft.resume.basic.name = "张三"
    store.checkpoint()
    store.draft.resume.basic.name = "李四"

    store.restoreCheckpoint()

    expect(store.draft.resume.basic.name).toBe("张三")
  })
})
