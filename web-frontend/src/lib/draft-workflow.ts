import type { DraftRecord, DraftSaveInput } from "./drafts"

export function removeDraftById<T extends { id: string }>(drafts: T[], id: string): T[] {
  return drafts.filter((draft) => draft.id !== id)
}

export function prependDraft<T>(drafts: T[], draft: T): T[] {
  return [draft, ...drafts]
}

export function toDraftSaveInput(draft: DraftRecord): DraftSaveInput {
  return {
    id: draft.id,
    jobTitle: draft.jobTitle,
    templateId: draft.templateId,
    resume: draft.resume,
    jobIntelligence: draft.jobIntelligence,
  }
}
