import { ref, watch, type WatchSource } from "vue"

import { createDebouncedTask } from "./debounced-task"

export type LocalSaveState = "idle" | "saving" | "saved" | "error"
export type ResumeFormSaveResult = "busy" | "invalid" | "saved" | "local-fallback"

type RegisterLifecycle = (handler: () => void) => void

export type ResumeFormOrchestrationOptions = {
  draft: WatchSource<unknown>
  resume: WatchSource<unknown>
  checkpoint(): void
  validate(): Record<string, string>
  saveRemote(): Promise<{ id: string }>
  applySavedId(id: string): void
  settleSavedId(): Promise<void>
  registerHide: RegisterLifecycle
  registerBeforeUnmount: RegisterLifecycle
}

export function createResumeFormOrchestration(options: ResumeFormOrchestrationOptions) {
  const localSaveState = ref<LocalSaveState>("idle")
  const fieldErrors = ref<Record<string, string>>({})
  const saving = ref(false)
  const validationActive = ref(false)
  let checkpointPaused = false

  const persistLocalCheckpoint = () => {
    try {
      options.checkpoint()
      localSaveState.value = "saved"
    } catch {
      localSaveState.value = "error"
    }
  }
  const localCheckpoint = createDebouncedTask(persistLocalCheckpoint, 800)

  watch(options.draft, () => {
    if (checkpointPaused) return
    localSaveState.value = "saving"
    localCheckpoint.schedule()
  }, { deep: true })

  watch(options.resume, () => {
    if (validationActive.value) fieldErrors.value = options.validate()
  }, { deep: true })

  const flush = () => localCheckpoint.flush()
  options.registerHide(flush)
  options.registerBeforeUnmount(flush)

  const save = async (): Promise<ResumeFormSaveResult> => {
    if (saving.value) return "busy"
    flush()
    validationActive.value = true
    fieldErrors.value = options.validate()
    if (Object.keys(fieldErrors.value).length) return "invalid"

    saving.value = true
    try {
      const saved = await options.saveRemote()
      checkpointPaused = true
      try {
        options.applySavedId(saved.id)
        await options.settleSavedId()
      } finally {
        checkpointPaused = false
      }
      localCheckpoint.cancel()
      persistLocalCheckpoint()
      return "saved"
    } catch {
      localCheckpoint.cancel()
      persistLocalCheckpoint()
      return "local-fallback"
    } finally {
      saving.value = false
    }
  }

  return { localSaveState, fieldErrors, saving, save }
}
