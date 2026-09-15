import { beforeEach, describe, expect, it } from "vitest"
import { createPinia, setActivePinia } from "pinia"

import { useCareerStore } from "../stores/career"
import { useApplicationsStore } from "../stores/applications"
import { useAssessmentStore } from "../stores/assessment"
import { useResumeStore } from "../stores/resume"
import { setAuthSession } from "../stores/session"
import { restoreLocalWorkspace } from "../utils/local-workspace"

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

describe("authenticated local workspace", () => {
  it("restores resume and career state after login", () => {
    setAuthSession("token-a", { userId: "user-a", phone: "13800138000" })
    const resume = useResumeStore()
    const career = useCareerStore()
    resume.draft.resume.basic.name = "用户 A"
    career.comparisonRoleNames = ["数据工程师"]
    resume.checkpoint()
    career.checkpoint()

    resume.resetDraft(false)
    career.resetPlanner(false)
    restoreLocalWorkspace()

    expect(resume.draft.resume.basic.name).toBe("用户 A")
    expect(career.comparisonRoleNames).toEqual(["数据工程师"])
  })

  it("does not retain the previous user's in-memory data when switching accounts", () => {
    setAuthSession("token-a", { userId: "user-a", phone: "13800138000" })
    const resume = useResumeStore()
    resume.draft.resume.basic.name = "用户 A"
    resume.checkpoint()

    setAuthSession("token-b", { userId: "user-b", phone: "13900139000" })
    restoreLocalWorkspace()

    expect(resume.draft.resume.basic.name).toBe("")
  })

  it("restores the current user's pending application queue", () => {
    setAuthSession("token-a", { userId: "user-a", phone: "13800138000" })
    storage.set("resume_demo_application_pending:user-a", [{ localId: "pending-1", roleName: "数据工程师" }])
    const applications = useApplicationsStore()

    restoreLocalWorkspace()

    expect(applications.pendingCount).toBe(1)
    expect(applications.pending[0].localId).toBe("pending-1")
  })

  it("clears previous assessment state when switching accounts", () => {
    setAuthSession("token-a", { userId: "user-a", phone: "13800138000" })
    const assessment = useAssessmentStore()
    assessment.answer("q1", 5)

    setAuthSession("token-b", { userId: "user-b", phone: "13900139000" })
    restoreLocalWorkspace()

    expect(assessment.answers).toEqual({})
    expect(assessment.result).toBeNull()
  })
})
