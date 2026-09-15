import { beforeEach, describe, expect, it } from "vitest"
import { createPinia, setActivePinia } from "pinia"

import { useApplicationsStore } from "../stores/applications"
import { setAuthSession } from "../stores/session"
import { clearLocalCareerWorkspace } from "../utils/local-privacy"

const storage = new Map<string, unknown>()

beforeEach(() => {
  storage.clear()
  setActivePinia(createPinia())
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
    removeStorageSync: (key: string) => storage.delete(key),
  }
})

describe("local career workspace privacy", () => {
  it("removes only workspace checkpoint and pending-queue keys", () => {
    storage.set("resume_demo_checkpoint", { draft: true })
    storage.set("resume_demo_application_pending", [{ roleName: "data engineer" }])
    storage.set("unrelated_key", "keep")

    clearLocalCareerWorkspace()

    expect(storage.has("resume_demo_checkpoint")).toBe(false)
    expect(storage.has("resume_demo_application_pending")).toBe(false)
    expect(storage.get("unrelated_key")).toBe("keep")
  })

  it("clears a queued application from memory during cleanup", () => {
    const applicationsStore = useApplicationsStore()
    applicationsStore.queuePending({
      clientId: "client-a",
      company: "Acme",
      roleName: "Data Engineer",
      city: "Shanghai",
      source: "official",
      status: "saved",
      appliedAt: null,
      nextActionAt: null,
      interviewNotes: "",
      draftId: null,
      notes: "",
    })

    clearLocalCareerWorkspace()
    applicationsStore.clearLocalData()

    expect(applicationsStore.pendingCount).toBe(0)
  })

  it("clears the authenticated user's scoped workspace keys", () => {
    setAuthSession("token-a", { userId: "user-a", phone: "13800138000" })
    storage.set("resume_demo_checkpoint:user-a", { draft: true })
    storage.set("resume_demo_application_pending:user-a", [{ roleName: "data engineer" }])
    storage.set("resume_demo_checkpoint:user-b", { draft: true })

    clearLocalCareerWorkspace()

    expect(storage.has("resume_demo_checkpoint:user-a")).toBe(false)
    expect(storage.has("resume_demo_application_pending:user-a")).toBe(false)
    expect(storage.has("resume_demo_checkpoint:user-b")).toBe(true)
  })
})
