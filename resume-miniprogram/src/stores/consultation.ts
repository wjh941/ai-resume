import { defineStore } from "pinia"

import type { ConsultationStage, IdentityCode } from "../types/consultation"

const CONSULTATION_STATE_KEY = "resume_demo_consultation_state"

export const IDENTITY_PROMPT =
  "请选择你当前求职身份（回复对应数字）：\n" +
  "1 - 在校学生（寻找短期实习）\n" +
  "2 - 应届毕业生（秋招/春招）\n" +
  "3 - 在职人员（想跳槽）\n" +
  "4 - 无业待业（有工作经验空档期）\n" +
  "5 - 零基础跨行业转行"

export const IDENTITY_OPTIONS: Array<{ code: IdentityCode; label: string }> = [
  { code: "1", label: "在校学生（寻找短期实习）" },
  { code: "2", label: "应届毕业生（秋招/春招）" },
  { code: "3", label: "在职人员（想跳槽）" },
  { code: "4", label: "无业待业（有工作经验空档期）" },
  { code: "5", label: "零基础跨行业转行" },
]

type UniStorage = {
  getStorageSync(key: string): unknown
  setStorageSync(key: string, value: unknown): void
}

function storage(): UniStorage | null {
  return (globalThis as typeof globalThis & { uni?: UniStorage }).uni ?? null
}

function isIdentityCode(value: unknown): value is IdentityCode {
  return typeof value === "string" && IDENTITY_OPTIONS.some((option) => option.code === value)
}

function identityLabel(code: IdentityCode | null): string {
  return IDENTITY_OPTIONS.find((option) => option.code === code)?.label ?? ""
}

export const useConsultationStore = defineStore("consultation", {
  state: () => ({
    stage: "role-entry" as ConsultationStage,
    pendingRoleName: "",
    identityCode: null as IdentityCode | null,
  }),
  getters: {
    identityLabel: (state) => identityLabel(state.identityCode),
  },
  actions: {
    beginIdentitySelection(roleName: string): void {
      this.pendingRoleName = roleName.trim()
      this.identityCode = null
      this.stage = "identity-selection"
      this.persist()
    },
    beginRoleConsultation(roleName: string): "identity-selection" | "reuse-identity" {
      this.pendingRoleName = roleName.trim()
      this.stage = this.identityCode ? "role-entry" : "identity-selection"
      this.persist()
      return this.identityCode ? "reuse-identity" : "identity-selection"
    },
    selectIdentity(identityCode: IdentityCode): void {
      this.identityCode = identityCode
      this.persist()
    },
    showJobAnalysis(): void {
      this.stage = "job-analysis"
      this.persist()
    },
    restore(): void {
      const saved = storage()?.getStorageSync(CONSULTATION_STATE_KEY)
      if (!saved || typeof saved !== "object") return
      const state = saved as {
        pendingRoleName?: unknown
        identityCode?: unknown
      }
      this.pendingRoleName = typeof state.pendingRoleName === "string" ? state.pendingRoleName : ""
      this.identityCode = isIdentityCode(state.identityCode) ? state.identityCode : null
      this.stage = "role-entry"
    },
    persist(): void {
      storage()?.setStorageSync(CONSULTATION_STATE_KEY, {
        pendingRoleName: this.pendingRoleName,
        identityCode: this.identityCode,
      })
    },
  },
})
