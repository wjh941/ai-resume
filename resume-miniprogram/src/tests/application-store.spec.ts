import { beforeEach, describe, expect, it } from "vitest"
import { createPinia, setActivePinia } from "pinia"

import { useApplicationsStore } from "../stores/applications"
import type { ApplicationInput } from "../types/application"

const storage = new Map<string, unknown>()
let networkAvailable = false

const input: ApplicationInput = {
  clientId: "client-a",
  company: "[待确认]",
  roleName: "数据工程师",
  city: "上海",
  source: "官网",
  status: "saved",
  appliedAt: null,
  nextActionAt: "2026-08-15",
  interviewNotes: "",
  draftId: null,
  notes: "",
}

beforeEach(() => {
  storage.clear()
  networkAvailable = false
  setActivePinia(createPinia())
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
    request: async () => {
      if (!networkAvailable) throw new Error("offline")
      return {
        statusCode: 200,
        data: {
          code: "ok",
          data: {
            id: "application-1",
            client_id: "client-a",
            company: "[待确认]",
            role_name: "数据工程师",
            city: "上海",
            source: "官网",
            status: "saved",
            applied_at: null,
            next_action_at: "2026-08-15",
            interview_notes: "",
            draft_id: null,
            notes: "",
            created_at: "2026-08-12T00:00:00+00:00",
            updated_at: "2026-08-12T00:00:00+00:00",
          },
        },
      }
    },
  }
})

describe("application pending queue", () => {
  it("keeps a failed application save in the local retry queue", async () => {
    const store = useApplicationsStore()

    await expect(store.saveOrQueue(input)).resolves.toEqual({ queued: true })
    expect(store.pendingCount).toBe(1)
    expect(storage.get("resume_demo_application_pending")).toBeTruthy()
  })

  it("replays queued application records after the network is available", async () => {
    const store = useApplicationsStore()
    await store.saveOrQueue(input)
    networkAvailable = true

    await expect(store.syncPending()).resolves.toEqual({ synced: 1, remaining: 0 })
    expect(store.pendingCount).toBe(0)
  })
})
