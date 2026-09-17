import { describe, expect, it } from "vitest"

import { clearApplicationCheckpoint, readApplicationCheckpoint, writeApplicationCheckpoint } from "../lib/application-checkpoint"
import { createApplicationFormSnapshot, type ApplicationFormSnapshot } from "../lib/application-form-state"

function memoryStorage(): Storage {
  const map = new Map<string, string>()
  return {
    get length() { return map.size },
    clear: () => map.clear(),
    getItem: (key: string) => map.get(key) ?? null,
    key: (index: number) => Array.from(map.keys())[index] ?? null,
    removeItem: (key: string) => { map.delete(key) },
    setItem: (key: string, value: string) => { map.set(key, value) },
  }
}

const snapshot: ApplicationFormSnapshot = createApplicationFormSnapshot(
  { company: "示例科技", roleName: "数据工程师", city: "上海", status: "saved", source: "官网", appliedAt: "2026-08-20", nextActionAt: "", nextInterviewAt: "2026-08-25T09:30", interviewNotes: "", notes: "", contactInfo: "", attachmentRef: "", draftId: "d-1" },
  { title: "投递跟进", description: "", occurredAt: "2026-08-21T10:00" },
  "2026-08-26T09:00",
)

describe("application checkpoint", () => {
  it("round-trips the form snapshot with a save time", () => {
    const storage = memoryStorage()
    writeApplicationCheckpoint(storage, snapshot, 1_755_000_000_000)
    const restored = readApplicationCheckpoint(storage)
    expect(restored).toEqual({ ...snapshot, savedAt: 1_755_000_000_000 })
  })

  it("returns null for corrupted, foreign or empty payloads", () => {
    const storage = memoryStorage()
    expect(readApplicationCheckpoint(storage)).toBeNull()
    storage.setItem("resume_web_applications_checkpoint", "{not json")
    expect(readApplicationCheckpoint(storage)).toBeNull()
    storage.setItem("resume_web_applications_checkpoint", JSON.stringify({ version: 2, savedAt: 1, snapshot }))
    expect(readApplicationCheckpoint(storage)).toBeNull()
    storage.setItem("resume_web_applications_checkpoint", JSON.stringify({ version: 1, savedAt: 1, snapshot: { ...snapshot, form: { ...snapshot.form, roleName: 42 } } }))
    expect(readApplicationCheckpoint(storage)).toBeNull()
  })

  it("clears the stored checkpoint", () => {
    const storage = memoryStorage()
    writeApplicationCheckpoint(storage, snapshot)
    clearApplicationCheckpoint(storage)
    expect(readApplicationCheckpoint(storage)).toBeNull()
    expect(() => clearApplicationCheckpoint(storage)).not.toThrow()
  })
})
