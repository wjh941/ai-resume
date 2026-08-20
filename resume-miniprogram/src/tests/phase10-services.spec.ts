import { beforeEach, describe, expect, it } from "vitest"

import { getAuthUser, setAuthSession } from "../stores/session"
import { mapResumeImportPreview } from "../services/resume-import-api"
import { listOperatorKnowledge } from "../services/operator-api"

const storage = new Map<string, unknown>()
const requests: Array<Record<string, unknown>> = []

beforeEach(() => {
  storage.clear()
  requests.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
    removeStorageSync: (key: string) => storage.delete(key),
    request: async (options: Record<string, unknown>) => {
      requests.push(options)
      return {
        statusCode: 200,
        data: {
          code: "ok",
          message: "",
          data: { items: [{ id: "item-1", title: "面试准备", content: "内容", status: "active", version: 1, created_at: "now", updated_at: "now" }] },
        },
      }
    },
  }
})

describe("Phase10 client services", () => {
  it("persists the operator role and keeps old stored users as ordinary users", () => {
    setAuthSession("token", { userId: "user-1", phone: "13800138000", role: "operator" })
    expect(getAuthUser()?.role).toBe("operator")

    storage.set("resume_demo_auth_user", { userId: "user-2", phone: "13900139000" })
    expect(getAuthUser()?.role).toBe("user")
  })

  it("maps a safe imported resume preview to the editor model", () => {
    const preview = mapResumeImportPreview({
      version: 1,
      basic: { name: "张三", phone: "13800138000", email: "zhang@example.com", city: "北京" },
      job: { target_role: "数据工程师", employment_type: "全职", expected_salary: "20k" },
      education: [], employment: [], projects: [],
      skills: { skills: ["Python"], certificates: [] }, self_evaluation: "认真负责",
      section_visibility: { basic: true, job: true, education: true, employment: true, projects: true, skills: true, self_evaluation: true },
    })

    expect(preview.job.targetRole).toBe("数据工程师")
    expect(preview.skills.englishLevel).toBe("")
    expect(preview.sectionVisibility.selfEvaluation).toBe(true)
  })

  it("requests operator knowledge with the stored JWT", async () => {
    setAuthSession("operator-token", { userId: "user-1", phone: "13800138000", role: "operator" })

    await expect(listOperatorKnowledge()).resolves.toMatchObject([{ id: "item-1", version: 1 }])

    expect(requests[0]).toMatchObject({
      url: "/api/operator/knowledge-items",
      header: { Authorization: "Bearer operator-token" },
    })
  })
})
