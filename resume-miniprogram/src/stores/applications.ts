import { defineStore } from "pinia"

import { isRetryableApiError } from "../services/http"
import { saveApplication } from "../services/application-api"
import type {
  ApplicationInput,
  ApplicationRecord,
  PendingApplication,
} from "../types/application"
import { deepClone as clone, getUniStorage as storage } from "../utils/persistence"
import { userStorageKey } from "./session"

const PENDING_KEY = "resume_demo_application_pending"
export { PENDING_KEY }

function newLocalId(): string {
  return `application-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

function fromPending(item: PendingApplication): ApplicationInput {
  const { localId: _, ...input } = item
  return input
}

export const useApplicationsStore = defineStore("applications", {
  state: () => ({
    pending: [] as PendingApplication[],
  }),
  getters: {
    pendingCount: (state) => state.pending.length,
  },
  actions: {
    restorePending(): void {
      const saved = storage()?.getStorageSync(userStorageKey(PENDING_KEY))
      if (!Array.isArray(saved)) return
      this.pending = clone(saved as PendingApplication[])
    },
    persistPending(): void {
      storage()?.setStorageSync(userStorageKey(PENDING_KEY), clone(this.pending))
    },
    queuePending(input: ApplicationInput): void {
      const index = this.pending.findIndex((item) => (
        input.id
          ? item.id === input.id
          : item.clientId === input.clientId
            && item.roleName === input.roleName
            && item.company === input.company
            && item.nextActionAt === input.nextActionAt
      ))
      const pending: PendingApplication = {
        ...clone(input),
        localId: index >= 0 ? this.pending[index].localId : newLocalId(),
      }
      if (index >= 0) this.pending.splice(index, 1, pending)
      else this.pending.push(pending)
      this.persistPending()
    },
    async saveOrQueue(input: ApplicationInput): Promise<{
      queued: boolean
      record?: ApplicationRecord
    }> {
      try {
        const record = await saveApplication(input)
        return { queued: false, record }
      } catch (error) {
        // 只有网络/服务器故障才进入离线队列；422 校验失败等业务错误直接抛给页面提示，
        // 否则非法数据会永远留在待同步队列里。
        if (!isRetryableApiError(error)) throw error
        this.queuePending(input)
        return { queued: true }
      }
    },
    async syncPending(): Promise<{ synced: number; remaining: number; skipped: number }> {
      this.restorePending()
      let synced = 0
      let skipped = 0
      for (const item of [...this.pending]) {
        try {
          await saveApplication(fromPending(item))
          this.pending = this.pending.filter((pending) => pending.localId !== item.localId)
          synced += 1
        } catch (error) {
          if (!isRetryableApiError(error)) {
            // 毒丸隔离：内容非法的记录跳过并计数，不再阻断队列中的其他记录。
            skipped += 1
            continue
          }
          // 网络/服务器不可用：停止本轮，保留剩余记录等待下次同步。
          break
        }
      }
      this.persistPending()
      return { synced, remaining: this.pending.length, skipped }
    },
    clearLocalData(): void {
      this.pending = []
      const localStorage = storage()
      const key = userStorageKey(PENDING_KEY)
      if (localStorage?.removeStorageSync) localStorage.removeStorageSync(key)
      else localStorage?.setStorageSync(key, [])
    },
  },
})
