import { defineStore } from "pinia"

import { createEmptyDraft, type JobIntelligence, type ResumeDraft } from "../types/resume"
import type { EvidenceSuggestion } from "../types/evidence"
import { applyEvidenceSuggestion as applyToDraft } from "../utils/evidence-suggestions"
import type { ResumeBackupState } from "../utils/local-backup"

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
    exportBackup(): ResumeBackupState {
      return clone({ activeJob: this.activeJob, draft: this.draft })
    },
    restoreBackup(snapshot: ResumeBackupState): boolean {
      if (!snapshot?.draft?.resume) return false
      this.activeJob = snapshot.activeJob ?? null
      this.draft = clone(snapshot.draft)
      this.checkpoint()
      return true
    },
    setJobIntelligence(job: JobIntelligence): void {
      this.activeJob = job
      this.draft.jobIntelligence = job
      if (!this.draft.jobTitle.trim()) this.draft.jobTitle = job.roleName
      if (!this.draft.resume.job.targetRole.trim()) this.draft.resume.job.targetRole = job.roleName
      this.checkpoint()
    },
    applyEvidenceSuggestion(suggestion: EvidenceSuggestion, checkpoint = true): boolean {
      const applied = applyToDraft(this.draft, suggestion)
      if (applied && checkpoint) this.checkpoint()
      return applied
    },
    resetDraft(checkpoint = true): void {
      this.activeJob = null
      this.draft = createEmptyDraft()
      if (checkpoint) this.checkpoint()
    },
  },
})
