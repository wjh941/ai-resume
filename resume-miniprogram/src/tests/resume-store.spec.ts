import { beforeEach, describe, expect, it } from "vitest"
import { createPinia, setActivePinia } from "pinia"

import { getClientId } from "../stores/session"
import { useResumeStore } from "../stores/resume"
import type { JobIntelligence } from "../types/resume"

const storage = new Map<string, unknown>()
const frontendJob: JobIntelligence = {
  version: 1,
  roleName: "前端开发工程师",
  salaryByExperience: {},
  responsibilities: [],
  hardRequirements: [],
  requiredSkills: [],
  bonusSkills: [],
  careerRoute: [],
}

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

  it("keeps user-entered job fields when a new role intelligence result is selected", () => {
    const store = useResumeStore()
    store.draft.jobTitle = "用户自定义岗位标题"
    store.draft.resume.job.targetRole = "用户自定义目标岗位"

    store.setJobIntelligence(frontendJob)
    const backup = store.exportBackup()
    store.resetDraft(false)

    expect(store.restoreBackup(backup)).toBe(true)
    expect(storage.get("resume_demo_checkpoint")).toBeTruthy()

    expect(store.activeJob).toEqual(frontendJob)
    expect(store.draft.jobIntelligence).toEqual(frontendJob)
    expect(store.draft.jobTitle).toBe("用户自定义岗位标题")
    expect(store.draft.resume.job.targetRole).toBe("用户自定义目标岗位")
  })
})
