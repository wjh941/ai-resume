import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { effectScope, nextTick, reactive, type EffectScope } from "vue"

import { createEmptyDraft, type ResumeDraft } from "../types/resume"
import { createResumeFormOrchestration } from "../utils/resume-form-orchestration"
import { toValidationErrorMap, validateResume } from "../utils/validators"

const scopes: EffectScope[] = []

beforeEach(() => vi.useFakeTimers())
afterEach(() => {
  scopes.splice(0).forEach((scope) => scope.stop())
  vi.clearAllTimers()
  vi.useRealTimers()
})

function makeValid(draft: ResumeDraft): void {
  draft.resume.basic.name = "Test User"
  draft.resume.basic.phone = "13800138000"
  draft.resume.basic.email = "test@example.com"
  draft.resume.job.targetRole = "Engineer"
}

function setup(options: {
  valid?: boolean
  checkpoint?: () => void
  saveRemote?: () => Promise<{ id: string }>
  observeSettledState?: (state: string) => void
} = {}) {
  const draft = reactive(createEmptyDraft())
  if (options.valid) makeValid(draft)
  const checkpoint = options.checkpoint ?? vi.fn()
  const saveRemote = options.saveRemote ?? vi.fn(async () => ({ id: "remote-id" }))
  let hideHandler: (() => void) | undefined
  let unmountHandler: (() => void) | undefined
  let controller!: ReturnType<typeof createResumeFormOrchestration>
  const scope = effectScope()
  scopes.push(scope)
  scope.run(() => {
    controller = createResumeFormOrchestration({
      draft: () => draft,
      resume: () => draft.resume,
      checkpoint,
      validate: () => toValidationErrorMap(validateResume(draft.resume)),
      saveRemote,
      applySavedId: (id) => { draft.id = id },
      settleSavedId: async () => {
        await nextTick()
        options.observeSettledState?.(controller.localSaveState.value)
      },
      registerHide: (handler) => { hideHandler = handler },
      registerBeforeUnmount: (handler) => { unmountHandler = handler },
    })
  })

  return {
    draft,
    checkpoint,
    saveRemote,
    controller,
    hide: () => {
      if (!hideHandler) throw new Error("hide handler was not registered")
      hideHandler()
    },
    unmount: () => {
      if (!unmountHandler) throw new Error("unmount handler was not registered")
      unmountHandler()
    },
  }
}

describe("createResumeFormOrchestration", () => {
  it("coalesces draft changes and settles the local status as saved", async () => {
    const { draft, checkpoint, saveRemote, controller } = setup()

    draft.resume.basic.name = "First"
    await nextTick()
    vi.advanceTimersByTime(500)
    draft.resume.basic.name = "Latest"
    await nextTick()
    vi.advanceTimersByTime(799)

    expect(checkpoint).not.toHaveBeenCalled()
    expect(controller.localSaveState.value).toBe("saving")
    vi.advanceTimersByTime(1)
    expect(checkpoint).toHaveBeenCalledTimes(1)
    expect(saveRemote).not.toHaveBeenCalled()
    expect(controller.localSaveState.value).toBe("saved")
  })

  it("flushes pending checkpoints from both lifecycle registrations", async () => {
    const { draft, checkpoint, saveRemote, hide, unmount } = setup()

    draft.resume.basic.name = "Hide"
    await nextTick()
    hide()
    draft.resume.basic.name = "Unmount"
    await nextTick()
    unmount()
    vi.runAllTimers()

    expect(checkpoint).toHaveBeenCalledTimes(2)
    expect(saveRemote).not.toHaveBeenCalled()
  })

  it("settles the local status as error when checkpoint storage fails", async () => {
    const { draft, controller } = setup({
      checkpoint: () => { throw new Error("storage full") },
    })

    draft.resume.basic.name = "Changed"
    await nextTick()
    vi.advanceTimersByTime(800)

    expect(controller.localSaveState.value).toBe("error")
  })

  it("catches a navigation-boundary checkpoint failure and cancels the delayed duplicate", async () => {
    const checkpoint = vi.fn(() => { throw new Error("storage full") })
    const navigate = vi.fn()
    const { draft, controller } = setup({ checkpoint })

    draft.resume.projects.push({ name: "Draft", role: "", startDate: "", endDate: "", description: "" })
    await nextTick()

    expect(() => {
      controller.flushLocalCheckpoint()
      navigate()
    }).not.toThrow()
    expect(controller.localSaveState.value).toBe("error")
    expect(navigate).toHaveBeenCalledTimes(1)
    vi.runAllTimers()
    expect(checkpoint).toHaveBeenCalledTimes(1)
  })

  it("flushes locally before invoking the remote API only from manual save", async () => {
    const events: string[] = []
    const checkpoint = vi.fn(() => events.push("checkpoint"))
    const saveRemote = vi.fn(async () => {
      events.push("remote")
      return { id: "remote-id" }
    })
    const { draft, controller } = setup({ valid: true, checkpoint, saveRemote })
    draft.resume.basic.city = "Shanghai"
    await nextTick()

    expect(saveRemote).not.toHaveBeenCalled()
    const saving = controller.save()
    expect(events.slice(0, 2)).toEqual(["checkpoint", "remote"])
    await expect(saving).resolves.toBe("saved")
    vi.runAllTimers()

    expect(saveRemote).toHaveBeenCalledTimes(1)
    expect(checkpoint).toHaveBeenCalledTimes(2)
    expect(controller.saving.value).toBe(false)
    expect(controller.localSaveState.value).toBe("saved")
  })

  it("keeps validation live after an invalid manual save", async () => {
    const { draft, saveRemote, controller } = setup()

    await expect(controller.save()).resolves.toBe("invalid")
    expect(Object.keys(controller.fieldErrors.value)).toEqual(expect.arrayContaining([
      "basic.name", "basic.phone", "basic.email", "job.targetRole",
    ]))
    expect(saveRemote).not.toHaveBeenCalled()

    draft.resume.basic.name = "Test User"
    await nextTick()
    expect(controller.fieldErrors.value["basic.name"]).toBeUndefined()
    expect(controller.fieldErrors.value["basic.phone"]).toBeTruthy()
  })

  it("does not schedule a delayed checkpoint while applying the returned ID", async () => {
    let stateAfterIdTick = ""
    const { draft, checkpoint, controller } = setup({
      valid: true,
      observeSettledState: (state) => { stateAfterIdTick = state },
    })

    await expect(controller.save()).resolves.toBe("saved")
    expect(draft.id).toBe("remote-id")
    expect(stateAfterIdTick).toBe("idle")
    expect(checkpoint).toHaveBeenCalledTimes(1)
    vi.runAllTimers()
    expect(checkpoint).toHaveBeenCalledTimes(1)
  })

  it("settles saving and preserves a local checkpoint after remote failure", async () => {
    const { checkpoint, controller } = setup({
      valid: true,
      saveRemote: vi.fn(async () => { throw new Error("offline") }),
    })

    await expect(controller.save()).resolves.toBe("local-fallback")
    expect(checkpoint).toHaveBeenCalledTimes(1)
    expect(controller.saving.value).toBe(false)
    expect(controller.localSaveState.value).toBe("saved")
  })
})
