import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { effectScope, nextTick, type EffectScope } from "vue"

import type { DraftRecord } from "../lib/drafts"
import { createResumeEditorOrchestration } from "../lib/resume-editor-orchestration"
import { validateDraft } from "../lib/resume-validation"

const scopes: EffectScope[] = []

beforeEach(() => vi.useFakeTimers())
afterEach(() => {
  scopes.splice(0).forEach((scope) => scope.stop())
  vi.clearAllTimers()
  vi.useRealTimers()
})

function validDraft(id = "d-1"): DraftRecord {
  return {
    id,
    jobTitle: "数据工程师简历",
    templateId: "business",
    resume: {
      version: 1,
      basic: { name: "张三", phone: "13800138000", email: "zhang@example.com", city: "上海" },
      job: { targetRole: "数据工程师", expectedSalary: "", employmentType: "" },
      education: [], employment: [], projects: [],
      skills: { skills: [], certificates: [] }, selfEvaluation: "",
      sectionVisibility: { basic: true, job: true, education: true, employment: true, projects: true, skills: true, selfEvaluation: true },
    },
    jobIntelligence: null,
    createdAt: "2026-08-24T09:00:00Z",
    updatedAt: "2026-08-24T10:00:00Z",
  }
}

function setup(options: {
  checkpoint?: (draft: DraftRecord) => void
  clearCheckpoint?: (draftId: string) => void
  restoreCheckpoint?: (serverDraft: DraftRecord) => DraftRecord | null
  saveRemote?: (draft: DraftRecord) => Promise<DraftRecord>
} = {}) {
  const checkpoint = options.checkpoint ?? vi.fn()
  const clearCheckpoint = options.clearCheckpoint ?? vi.fn()
  const saveRemote = options.saveRemote ?? vi.fn(async (draft: DraftRecord) => ({
    ...draft,
    updatedAt: "2026-08-24T12:00:00Z",
  }))
  const onSaved = vi.fn()
  const onRemoteError = vi.fn()
  let unmountHandler: (() => void) | undefined
  let controller!: ReturnType<typeof createResumeEditorOrchestration>
  const scope = effectScope()
  scopes.push(scope)
  scope.run(() => {
    controller = createResumeEditorOrchestration({
      checkpoint,
      clearCheckpoint,
      restoreCheckpoint: options.restoreCheckpoint ?? (() => null),
      validate: validateDraft,
      saveRemote,
      settleDraft: nextTick,
      onSaved,
      onRemoteError,
      registerBeforeUnmount: (handler) => { unmountHandler = handler },
    })
  })

  return {
    checkpoint,
    clearCheckpoint,
    saveRemote,
    onSaved,
    onRemoteError,
    controller,
    unmount: () => {
      if (!unmountHandler) throw new Error("unmount handler was not registered")
      unmountHandler()
    },
  }
}

describe("createResumeEditorOrchestration", () => {
  it("suppresses hydration and debounces later local-only changes", async () => {
    const { checkpoint, saveRemote, controller } = setup()

    await controller.hydrate(validDraft())
    expect(controller.isDirty.value).toBe(false)
    vi.runAllTimers()
    expect(checkpoint).not.toHaveBeenCalled()

    controller.draft.value!.resume.basic.city = "北京"
    await nextTick()
    expect(controller.isDirty.value).toBe(true)
    vi.advanceTimersByTime(500)
    controller.draft.value!.resume.basic.city = "深圳"
    await nextTick()
    vi.advanceTimersByTime(799)
    expect(controller.localSaveState.value).toBe("saving")
    expect(checkpoint).not.toHaveBeenCalled()
    expect(saveRemote).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1)
    expect(checkpoint).toHaveBeenCalledTimes(1)
    expect(checkpoint).toHaveBeenLastCalledWith(controller.draft.value)
    expect(controller.localSaveState.value).toBe("saved")
  })

  it("starts dirty when hydration restores a newer checkpoint", async () => {
    const checkpoint = validDraft()
    checkpoint.resume.basic.city = "Beijing"
    checkpoint.updatedAt = "2026-08-24T11:00:00Z"
    const { controller } = setup({ restoreCheckpoint: () => checkpoint })

    await controller.hydrate(validDraft())

    expect(controller.isDirty.value).toBe(true)
  })

  it("falls back to the server draft when storage access fails during hydration", async () => {
    const serverDraft = validDraft()
    const { checkpoint, onRemoteError, controller } = setup({
      restoreCheckpoint: () => { throw new DOMException("blocked", "SecurityError") },
    })

    await controller.hydrate(serverDraft)
    vi.runAllTimers()

    expect(controller.draft.value).toMatchObject({ id: "d-1", jobTitle: "数据工程师简历" })
    expect(controller.localSaveState.value).toBe("error")
    expect(checkpoint).not.toHaveBeenCalled()
    expect(onRemoteError).not.toHaveBeenCalled()
  })

  it("flushes on unmount and settles checkpoint errors", async () => {
    const { controller, unmount } = setup({
      checkpoint: () => { throw new Error("storage full") },
    })
    await controller.hydrate(validDraft())

    controller.draft.value!.resume.basic.city = "杭州"
    await nextTick()
    unmount()
    vi.runAllTimers()

    expect(controller.localSaveState.value).toBe("error")
  })

  it("cancels a pending checkpoint before discard and unmount", async () => {
    const { checkpoint, clearCheckpoint, controller, unmount } = setup()
    await controller.hydrate(validDraft())

    controller.draft.value!.resume.basic.city = "discarded"
    await nextTick()
    controller.discardLocalCheckpoint()
    unmount()
    vi.runAllTimers()

    expect(clearCheckpoint).toHaveBeenCalledWith("d-1")
    expect(checkpoint).not.toHaveBeenCalled()
  })

  it("recovers after a failed checkpoint write", async () => {
    let attempts = 0
    const { controller } = setup({
      checkpoint: () => {
        attempts += 1
        if (attempts === 1) throw new Error("storage full")
      },
    })
    await controller.hydrate(validDraft())

    controller.draft.value!.resume.basic.city = "首次失败"
    await nextTick()
    vi.advanceTimersByTime(800)
    expect(controller.localSaveState.value).toBe("error")

    controller.draft.value!.resume.basic.city = "再次保存"
    await nextTick()
    expect(controller.localSaveState.value).toBe("saving")
    vi.advanceTimersByTime(800)

    expect(attempts).toBe(2)
    expect(controller.localSaveState.value).toBe("saved")
  })

  it("keeps validation live after an invalid manual save", async () => {
    const { saveRemote, controller } = setup()
    const draft = validDraft()
    draft.jobTitle = ""
    draft.resume.basic.name = ""
    await controller.hydrate(draft)

    await expect(controller.save()).resolves.toBe("invalid")
    expect(controller.fieldErrors.value.jobTitle).toBeTruthy()
    expect(controller.fieldErrors.value["basic.name"]).toBeTruthy()
    expect(saveRemote).not.toHaveBeenCalled()

    controller.draft.value!.resume.basic.name = "李四"
    await nextTick()
    expect(controller.fieldErrors.value["basic.name"]).toBeUndefined()
    expect(controller.fieldErrors.value.jobTitle).toBeTruthy()
  })

  it("flushes locally before the manual remote save and clears on success", async () => {
    const events: string[] = []
    const { onSaved, controller } = setup({
      checkpoint: () => { events.push("checkpoint") },
      clearCheckpoint: () => { events.push("clear") },
      saveRemote: async (draft) => {
        events.push("remote")
        return { ...draft, updatedAt: "2026-08-24T12:00:00Z" }
      },
    })
    await controller.hydrate(validDraft())
    controller.draft.value!.resume.basic.city = "成都"
    await nextTick()

    await expect(controller.save()).resolves.toBe("saved")
    expect(controller.isDirty.value).toBe(false)
    expect(events).toEqual(["checkpoint", "remote", "clear"])
    expect(onSaved).toHaveBeenCalledTimes(1)
    expect(controller.saving.value).toBe(false)
  })

  it("keeps storage-clear failures out of the remote API error state", async () => {
    const { onSaved, onRemoteError, controller } = setup({
      clearCheckpoint: () => { throw new Error("storage blocked") },
    })
    await controller.hydrate(validDraft())

    await expect(controller.save()).resolves.toBe("saved")
    expect(controller.localSaveState.value).toBe("error")
    expect(onRemoteError).not.toHaveBeenCalled()
    expect(onSaved).toHaveBeenCalledTimes(1)
  })

  it("prevents concurrent duplicate remote saves", async () => {
    let resolveRemote!: (draft: DraftRecord) => void
    const remoteResult = new Promise<DraftRecord>((resolve) => { resolveRemote = resolve })
    const saveRemote = vi.fn(() => remoteResult)
    const { controller } = setup({ saveRemote })
    await controller.hydrate(validDraft())

    const firstSave = controller.save()
    const secondSave = controller.save()
    expect(saveRemote).toHaveBeenCalledTimes(1)

    resolveRemote(validDraft())
    await expect(secondSave).resolves.toBe("busy")
    await expect(firstSave).resolves.toBe("saved")
    expect(saveRemote).toHaveBeenCalledTimes(1)
  })

  it("does not recreate a checkpoint after replacing the draft from the server", async () => {
    const { checkpoint, controller } = setup()
    await controller.hydrate(validDraft())

    await expect(controller.save()).resolves.toBe("saved")
    vi.runAllTimers()

    expect(checkpoint).not.toHaveBeenCalled()
    expect(controller.localSaveState.value).toBe("idle")
  })

  it("preserves edits made while the remote save is in flight", async () => {
    let resolveRemote!: (draft: DraftRecord) => void
    const checkpointedCities: string[] = []
    const { clearCheckpoint, onSaved, controller } = setup({
      checkpoint: (draft) => { checkpointedCities.push(draft.resume.basic.city) },
      saveRemote: () => new Promise((resolve) => { resolveRemote = resolve }),
    })
    await controller.hydrate(validDraft())
    controller.draft.value!.resume.basic.city = "保存前"
    await nextTick()

    const saving = controller.save()
    controller.draft.value!.resume.basic.city = "保存中修改"
    await nextTick()
    const saved = validDraft()
    saved.resume.basic.city = "保存前"
    saved.updatedAt = "2026-08-24T12:00:00Z"
    resolveRemote(saved)

    await expect(saving).resolves.toBe("saved")
    expect(controller.draft.value!.resume.basic.city).toBe("保存中修改")
    expect(checkpointedCities).toEqual(["保存前", "保存中修改"])
    expect(controller.isDirty.value).toBe(true)
    expect(clearCheckpoint).not.toHaveBeenCalled()
    expect(onSaved).toHaveBeenCalledWith(saved)
  })

  it("retains dirty state when the remote save fails", async () => {
    const { controller, onRemoteError } = setup({
      saveRemote: async () => { throw new Error("offline") },
    })
    await controller.hydrate(validDraft())
    controller.draft.value!.resume.basic.city = "failed"
    await nextTick()

    await expect(controller.save()).resolves.toBe("error")

    expect(controller.isDirty.value).toBe(true)
    expect(onRemoteError).toHaveBeenCalledTimes(1)
  })

  it("preserves a changed checkpoint after unmounting during remote save", async () => {
    let resolveRemote!: (draft: DraftRecord) => void
    const checkpointedCities: string[] = []
    const { clearCheckpoint, onSaved, controller, unmount } = setup({
      checkpoint: (draft) => { checkpointedCities.push(draft.resume.basic.city) },
      saveRemote: () => new Promise((resolve) => { resolveRemote = resolve }),
    })
    await controller.hydrate(validDraft())
    controller.draft.value!.resume.basic.city = "保存前"
    await nextTick()

    const saving = controller.save()
    controller.draft.value!.resume.basic.city = "离开前修改"
    await nextTick()
    unmount()
    resolveRemote(validDraft())

    await expect(saving).resolves.toBe("saved")
    expect(checkpointedCities).toEqual(["保存前", "离开前修改"])
    expect(clearCheckpoint).not.toHaveBeenCalled()
    expect(onSaved).not.toHaveBeenCalled()
  })

  it("clears an unchanged checkpoint after unmounting during a successful save", async () => {
    let resolveRemote!: (draft: DraftRecord) => void
    const { checkpoint, clearCheckpoint, onSaved, controller, unmount } = setup({
      saveRemote: () => new Promise((resolve) => { resolveRemote = resolve }),
    })
    await controller.hydrate(validDraft())
    controller.draft.value!.resume.basic.city = "保存前"
    await nextTick()

    const saving = controller.save()
    unmount()
    resolveRemote(validDraft())

    await expect(saving).resolves.toBe("saved")
    expect(checkpoint).toHaveBeenCalledTimes(1)
    expect(clearCheckpoint).toHaveBeenCalledWith("d-1")
    expect(onSaved).not.toHaveBeenCalled()
    expect(controller.saving.value).toBe(false)
  })
})
