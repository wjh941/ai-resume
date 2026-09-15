import { defineStore } from "pinia"

import { createEmptyDraft, type JobIntelligence, type ResumeDraft } from "../types/resume"
import type { EvidenceSuggestion } from "../types/evidence"
import { applyEvidenceSuggestion as applyToDraft } from "../utils/evidence-suggestions"
import type { ResumeBackupState } from "../utils/local-backup"
import { deepClone as clone, getUniStorage as storage } from "../utils/persistence"
import { userStorageKey } from "./session"

const CHECKPOINT_KEY = "resume_demo_checkpoint"
export { CHECKPOINT_KEY }

export const useResumeStore = defineStore("resume", {
  state: () => ({
    activeJob: null as JobIntelligence | null,
    draft: createEmptyDraft() as ResumeDraft,
  }),
  actions: {
    checkpoint(): void {
      storage()?.setStorageSync(userStorageKey(CHECKPOINT_KEY), clone({ activeJob: this.activeJob, draft: this.draft }))
    },
    restoreCheckpoint(): void {
      const saved = storage()?.getStorageSync(userStorageKey(CHECKPOINT_KEY))
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
