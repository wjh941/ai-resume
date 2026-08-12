import { defineStore } from "pinia"

import { saveApplication } from "../services/application-api"
import type {
  ApplicationInput,
  ApplicationRecord,
  PendingApplication,
} from "../types/application"

const PENDING_KEY = "resume_demo_application_pending"

type UniStorage = {
  getStorageSync(key: string): unknown
  setStorageSync(key: string, value: unknown): void
  removeStorageSync?(key: string): void
}

function storage(): UniStorage | null {
  return (globalThis as typeof globalThis & { uni?: UniStorage }).uni ?? null
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

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
      const saved = storage()?.getStorageSync(PENDING_KEY)
      if (!Array.isArray(saved)) return
      this.pending = clone(saved as PendingApplication[])
    },
    persistPending(): void {
      storage()?.setStorageSync(PENDING_KEY, clone(this.pending))
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
      } catch {
        this.queuePending(input)
        return { queued: true }
      }
    },
    async syncPending(): Promise<{ synced: number; remaining: number }> {
      this.restorePending()
      let synced = 0
      for (const item of [...this.pending]) {
        try {
          await saveApplication(fromPending(item))
          this.pending = this.pending.filter((pending) => pending.localId !== item.localId)
          synced += 1
        } catch {
          break
        }
      }
      this.persistPending()
      return { synced, remaining: this.pending.length }
    },
    clearLocalData(): void {
      this.pending = []
      const localStorage = storage()
      if (localStorage?.removeStorageSync) localStorage.removeStorageSync(PENDING_KEY)
      else localStorage?.setStorageSync(PENDING_KEY, [])
    },
  },
})
