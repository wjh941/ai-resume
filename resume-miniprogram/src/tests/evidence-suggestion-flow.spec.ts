import { beforeEach, describe, expect, it } from "vitest"
import { createPinia, setActivePinia } from "pinia"

import { useResumeStore } from "../stores/resume"
import type { EvidenceSuggestion } from "../types/evidence"


const storage = new Map<string, unknown>()
const projectSuggestion: EvidenceSuggestion = {
  sourceEvidenceId: "evidence-1",
  sourceTitle: "Data pipeline",
  targetSection: "project",
  title: "Data pipeline",
  role: "Data Engineer related experience",
  description: "Action: built validation",
  riskNote: "",
}


beforeEach(() => {
  storage.clear()
  setActivePinia(createPinia())
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
  }
})


describe("evidence suggestion resume flow", () => {
  it("checkpoints only after applying a suggestion to an empty section", () => {
    const store = useResumeStore()

    expect(store.applyEvidenceSuggestion(projectSuggestion)).toBe(true)
    expect(store.draft.resume.projects).toEqual([{
      name: "Data pipeline",
      role: "Data Engineer related experience",
      startDate: "[待确认]",
      endDate: "[待确认]",
      description: "Action: built validation",
    }])
    const saved = storage.get("resume_demo_checkpoint")

    expect(store.applyEvidenceSuggestion(projectSuggestion)).toBe(false)
    expect(store.draft.resume.projects).toHaveLength(1)
    expect(storage.get("resume_demo_checkpoint")).toEqual(saved)
  })
})
