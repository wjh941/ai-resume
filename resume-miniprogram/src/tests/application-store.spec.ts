import { beforeEach, describe, expect, it } from "vitest"
import { createPinia, setActivePinia } from "pinia"

import { useApplicationsStore } from "../stores/applications"
import { setAuthSession } from "../stores/session"
import type { ApplicationInput } from "../types/application"

const storage = new Map<string, unknown>()

type FailureMode = "offline" | "validation" | "server"
let failureMode: FailureMode | null = null
let callCount = 0

const savedRecord = {
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
}

function respond(): { statusCode: number; data: unknown } {
  callCount += 1
  if (!failureMode) return { statusCode: 200, data: { code: "ok", data: savedRecord } }
  if (failureMode === "offline") throw new Error("offline")
  if (failureMode === "validation") {
    return { statusCode: 422, data: { code: "validation_error", message: "请求校验失败", data: {} } }
  }
  return { statusCode: 500, data: { code: "database_error", message: "数据库操作失败", data: {} } }
}

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
  failureMode = null
  callCount = 0
  setActivePinia(createPinia())
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
    request: async () => respond(),
  }
})

describe("application pending queue", () => {
  it("keeps a failed application save in the local retry queue", async () => {
    failureMode = "offline"
    const store = useApplicationsStore()

    await expect(store.saveOrQueue(input)).resolves.toEqual({ queued: true })
    expect(store.pendingCount).toBe(1)
    expect(storage.get("resume_demo_application_pending")).toBeTruthy()
  })

  it("keeps the save in the queue when the server itself is broken (5xx)", async () => {
    failureMode = "server"
    const store = useApplicationsStore()

    await expect(store.saveOrQueue(input)).resolves.toEqual({ queued: true })
    expect(store.pendingCount).toBe(1)
  })

  it("rejects validation failures without queueing them", async () => {
    failureMode = "validation"
    const store = useApplicationsStore()

    await expect(store.saveOrQueue(input)).rejects.toMatchObject({ kind: "business" })
    expect(store.pendingCount).toBe(0)
    expect(storage.get("resume_demo_application_pending")).toBeUndefined()
  })

  it("replays queued application records after the network is available", async () => {
    const store = useApplicationsStore()
    failureMode = "offline"
    await store.saveOrQueue(input)
    failureMode = null

    await expect(store.syncPending()).resolves.toEqual({ synced: 1, remaining: 0, skipped: 0 })
    expect(store.pendingCount).toBe(0)
  })

  it("skips invalid queued records without blocking the rest of the queue", async () => {
    const store = useApplicationsStore()
    failureMode = "offline"
    await store.saveOrQueue({ ...input, clientId: "client-bad" })
    await store.saveOrQueue({ ...input, clientId: "client-good" })
    expect(store.pendingCount).toBe(2)

    // 毒丸记录（422）跳过；后续合法记录继续同步。
    failureMode = "validation"
    const first = await store.syncPending()
    expect(first).toEqual({ synced: 0, remaining: 2, skipped: 2 })

    failureMode = null
    const second = await store.syncPending()
    expect(second.synced).toBe(2)
    expect(store.pendingCount).toBe(0)
  })

  it("stops the sync round when the network is still unavailable", async () => {
    const store = useApplicationsStore()
    failureMode = "offline"
    await store.saveOrQueue(input)
    await store.saveOrQueue({ ...input, clientId: "client-b" })
    failureMode = null
    let calls = 0
    ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
      getStorageSync: (key: string) => storage.get(key),
      setStorageSync: (key: string, value: unknown) => storage.set(key, value),
      request: async () => {
        calls += 1
        if (calls === 1) throw new Error("offline")
        return { statusCode: 200, data: { code: "ok", data: savedRecord } }
      },
    }

    const result = await store.syncPending()

    expect(result).toEqual({ synced: 0, remaining: 2, skipped: 0 })
    expect(calls).toBe(1)
  })

  it("stores pending applications under the authenticated user namespace", async () => {
    setAuthSession("token-a", { userId: "user-a", phone: "13800138000" })
    const store = useApplicationsStore()

    failureMode = "offline"
    await store.saveOrQueue(input)

    expect(storage.get("resume_demo_application_pending:user-a")).toBeTruthy()
    expect(storage.get("resume_demo_application_pending:user-b")).toBeUndefined()
  })
})
