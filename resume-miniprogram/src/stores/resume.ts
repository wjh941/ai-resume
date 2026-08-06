import { defineStore } from "pinia"

import { createEmptyDraft, type JobIntelligence, type ResumeDraft } from "../types/resume"

const CHECKPOINT_KEY = "resume_demo_checkpoint"

type UniStorage = {
  getStorageSync(key: string): unknown
  setStorageSync(key: string, value: unknown): void
}

function storage(): UniStorage | null {
  return (globalThis as typeof globalThis & { uni?: UniStorage }).uni ?? null
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

export const useResumeStore = defineStore("resume", {
  state: () => ({
    activeJob: null as JobIntelligence | null,
    draft: createEmptyDraft() as ResumeDraft,
  }),
  actions: {
    checkpoint(): void {
      storage()?.setStorageSync(CHECKPOINT_KEY, clone({ activeJob: this.activeJob, draft: this.draft }))
    },
    restoreCheckpoint(): void {
      const saved = storage()?.getStorageSync(CHECKPOINT_KEY)
      if (!saved || typeof saved !== "object") return
      const checkpoint = saved as { activeJob?: JobIntelligence | null; draft?: ResumeDraft }
      if (checkpoint.draft) this.draft = clone(checkpoint.draft)
      this.activeJob = checkpoint.activeJob ?? null
    },
    setJobIntelligence(job: JobIntelligence): void {
      this.activeJob = job
      this.draft.jobIntelligence = job
      this.draft.jobTitle = job.roleName
      this.draft.resume.job.targetRole = job.roleName
      this.checkpoint()
    },
    resetDraft(): void {
      this.activeJob = null
      this.draft = createEmptyDraft()
      this.checkpoint()
    },
  },
})
