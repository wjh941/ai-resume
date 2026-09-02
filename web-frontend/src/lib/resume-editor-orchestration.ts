import { ref, watch, type Ref } from "vue"

import { createDebouncedTask } from "./debounced-task"
import type { DraftRecord } from "./drafts"

export type LocalSaveState = "idle" | "saving" | "saved" | "error"
export type ResumeEditorSaveResult = "busy" | "invalid" | "saved" | "error"

type RegisterLifecycle = (handler: () => void) => void

export type ResumeEditorOrchestrationOptions = {
  checkpoint(draft: DraftRecord): void
  clearCheckpoint(draftId: string): void
  restoreCheckpoint(serverDraft: DraftRecord): DraftRecord | null
  validate(draft: DraftRecord): Record<string, string>
  saveRemote(draft: DraftRecord): Promise<DraftRecord>
  settleDraft(): Promise<void>
  onSaveStart?(): void
  onSaved(draft: DraftRecord): void
  onRemoteError(): void
  registerBeforeUnmount: RegisterLifecycle
}

export function createResumeEditorOrchestration(options: ResumeEditorOrchestrationOptions): {
  draft: ReturnType<typeof ref<DraftRecord | null>>
  fieldErrors: ReturnType<typeof ref<Record<string, string>>>
  validationActive: ReturnType<typeof ref<boolean>>
  localSaveState: ReturnType<typeof ref<LocalSaveState>>
  hydrated: ReturnType<typeof ref<boolean>>
  saving: ReturnType<typeof ref<boolean>>
  isDirty: Ref<boolean>
  hydrate: (serverDraft: DraftRecord) => Promise<void>
  discardLocalCheckpoint: (draftId?: string) => void
  save: () => Promise<ResumeEditorSaveResult>
} {
  const draft = ref<DraftRecord | null>(null)
  const fieldErrors = ref<Record<string, string>>({})
  const validationActive = ref(false)
  const localSaveState = ref<LocalSaveState>("idle")
  const hydrated = ref(false)
  const saving = ref(false)
  const isDirty = ref(false)
  let checkpointPaused = false
  let draftRevision = 0
  let unmounted = false

  const persistLocalCheckpoint = () => {
    if (!draft.value) return
    try {
      options.checkpoint(draft.value)
      localSaveState.value = "saved"
    } catch {
      localSaveState.value = "error"
      isDirty.value = true
    }
  }
  const localCheckpoint = createDebouncedTask(persistLocalCheckpoint, 800)

  watch(draft, (currentDraft) => {
    if (!currentDraft) return
    if (validationActive.value) fieldErrors.value = options.validate(currentDraft)
    if (!hydrated.value || checkpointPaused) return
    isDirty.value = true
    draftRevision += 1
    localSaveState.value = "saving"
    localCheckpoint.schedule()
  }, { deep: true })

  const flush = () => localCheckpoint.flush()
  const discardLocalCheckpoint = (draftId?: string): void => {
    localCheckpoint.cancel()
    const id = draft.value?.id ?? draftId
    if (id) options.clearCheckpoint(id)
  }
  options.registerBeforeUnmount(() => {
    unmounted = true
    flush()
  })

  const hydrate = async (serverDraft: DraftRecord): Promise<void> => {
    let loaded = serverDraft
    try {
      loaded = options.restoreCheckpoint(serverDraft) || serverDraft
    } catch {
      localSaveState.value = "error"
    }
    checkpointPaused = true
    try {
      draft.value = loaded
      isDirty.value = loaded !== serverDraft
      await options.settleDraft()
      hydrated.value = true
    } finally {
      checkpointPaused = false
    }
  }

  const save = async (): Promise<ResumeEditorSaveResult> => {
    if (!draft.value || saving.value) return "busy"
    localCheckpoint.flush()
    options.onSaveStart?.()
    validationActive.value = true
    fieldErrors.value = options.validate(draft.value)
    if (Object.keys(fieldErrors.value).length) {
      isDirty.value = true
      return "invalid"
    }
    const savedRevision = draftRevision

    saving.value = true
    try {
      const saved = await options.saveRemote(draft.value)
      if (draftRevision !== savedRevision) {
        isDirty.value = true
        localCheckpoint.flush()
        if (!unmounted) options.onSaved(saved)
        return "saved"
      }
      localCheckpoint.cancel()
      isDirty.value = false
      if (unmounted) {
        try {
          options.clearCheckpoint(saved.id)
        } catch {
          // The editor is detached, so there is no local status surface to update.
        }
        return "saved"
      }
      checkpointPaused = true
      try {
        draft.value = saved
        await options.settleDraft()
        try {
          options.clearCheckpoint(saved.id)
        } catch {
          localSaveState.value = "error"
        }
      } finally {
        checkpointPaused = false
      }
      options.onSaved(saved)
      return "saved"
    } catch {
      isDirty.value = true
      options.onRemoteError()
      return "error"
    } finally {
      saving.value = false
    }
  }

  return { draft, fieldErrors, validationActive, localSaveState, hydrated, saving, isDirty, hydrate, discardLocalCheckpoint, save }
}
