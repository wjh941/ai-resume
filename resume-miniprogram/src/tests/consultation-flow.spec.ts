import { beforeEach, describe, expect, it } from "vitest"
import { createPinia, setActivePinia } from "pinia"

import { IDENTITY_PROMPT, useConsultationStore } from "../stores/consultation"

const storage = new Map<string, unknown>()

beforeEach(() => {
  storage.clear()
  setActivePinia(createPinia())
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
  }
})

describe("consultation flow", () => {
  it("shows only the identity prompt after the first role query", () => {
    const store = useConsultationStore()

    store.beginIdentitySelection("数据工程师")

    expect(store.stage).toBe("identity-selection")
    expect(store.pendingRoleName).toBe("数据工程师")
    expect(store.identityCode).toBeNull()
    expect(IDENTITY_PROMPT).toBe(
      "请选择你当前求职身份（回复对应数字）：\n1 - 在校学生（寻找短期实习）\n2 - 应届毕业生（秋招/春招）\n3 - 在职人员（想跳槽）\n4 - 无业待业（有工作经验空档期）\n5 - 零基础跨行业转行",
    )
  })

  it("persists the selected identity for later resume review", () => {
    const store = useConsultationStore()
    store.beginIdentitySelection("数据工程师")

    store.selectIdentity("3")

    expect(store.identityCode).toBe("3")
    expect(store.identityLabel).toBe("在职人员（想跳槽）")

    setActivePinia(createPinia())
    const restored = useConsultationStore()
    restored.restore()
    expect(restored.identityCode).toBe("3")
    expect(restored.pendingRoleName).toBe("数据工程师")
  })
})
