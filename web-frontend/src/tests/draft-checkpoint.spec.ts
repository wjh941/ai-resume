import { beforeEach, describe, expect, it } from "vitest"

import {
  checkpointKey,
  clearDraftCheckpoint,
  readDraftCheckpoint,
  writeDraftCheckpoint,
} from "../lib/draft-checkpoint"
import type { DraftRecord } from "../lib/drafts"

const values = new Map<string, string>()
const storage = {
  getItem: (key: string) => values.get(key) ?? null,
  setItem: (key: string, value: string) => { values.set(key, value) },
  removeItem: (key: string) => { values.delete(key) },
}
const draft: DraftRecord = {
  id: "d-1",
  jobTitle: "数据工程师简历",
  templateId: "business",
  resume: {
    version: 1,
    basic: { name: "张三", phone: "13800138000", email: "zhang@example.com", city: "上海" },
    job: { targetRole: "数据工程师", expectedSalary: "", employmentType: "" },
    education: [],
    employment: [],
    projects: [],
    skills: { skills: [], certificates: [] },
    selfEvaluation: "",
    sectionVisibility: { basic: true, job: true, education: true, employment: true, projects: true, skills: true, selfEvaluation: true },
  },
  jobIntelligence: null,
  createdAt: "2026-08-24T09:00:00Z",
  updatedAt: "2026-08-24T10:00:00Z",
}

beforeEach(() => values.clear())

it("restores only a newer matching checkpoint", () => {
  writeDraftCheckpoint(storage, draft, Date.parse("2026-08-24T09:00:00Z"))
  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toBeNull()

  writeDraftCheckpoint(storage, draft, Date.parse("2026-08-24T11:00:00Z"))
  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toMatchObject({ id: "d-1" })
})

it("rejects a checkpoint when the server timestamp is invalid", () => {
  writeDraftCheckpoint(storage, draft, Date.parse("2026-08-24T11:00:00Z"))

  expect(readDraftCheckpoint(storage, "d-1", "not-a-server-timestamp")).toBeNull()
})

it("rejects unsupported checkpoint versions", () => {
  storage.setItem(checkpointKey("d-1"), JSON.stringify({
    version: 2,
    draftId: "d-1",
    savedAt: Date.parse("2026-08-24T11:00:00Z"),
    draft,
  }))

  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toBeNull()
})

it("restores the existing backend-shaped section visibility", () => {
  const backendDraft = JSON.parse(JSON.stringify(draft)) as DraftRecord
  backendDraft.resume.sectionVisibility = {
    basic: true,
    job: true,
    education: true,
    employment: true,
    projects: true,
    skills: true,
    self_evaluation: true,
  } as unknown as DraftRecord["resume"]["sectionVisibility"]

  writeDraftCheckpoint(storage, backendDraft, Date.parse("2026-08-24T11:00:00Z"))

  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toMatchObject({ id: "d-1" })
})

it("ignores mismatched and malformed checkpoint data", () => {
  storage.setItem(checkpointKey("d-1"), JSON.stringify({
    version: 1,
    draftId: "other",
    savedAt: Date.parse("2026-08-24T11:00:00Z"),
    draft,
  }))
  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toBeNull()

  storage.setItem(checkpointKey("d-1"), "not-json")
  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toBeNull()

  storage.setItem(checkpointKey("d-1"), JSON.stringify({
    version: 1,
    draftId: "d-1",
    savedAt: Date.parse("2026-08-24T11:00:00Z"),
    draft: { id: "d-1" },
  }))
  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toBeNull()
})

it("rejects a newer checkpoint that the editor cannot consume", () => {
  storage.setItem(checkpointKey("d-1"), JSON.stringify({
    version: 1,
    draftId: "d-1",
    savedAt: Date.parse("2026-08-24T11:00:00Z"),
    draft: {
      id: "d-1",
      jobTitle: "数据工程师简历",
      resume: { basic: {}, job: {} },
    },
  }))

  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toBeNull()
})

it("clears a saved checkpoint after remote save", () => {
  writeDraftCheckpoint(storage, draft)
  clearDraftCheckpoint(storage, "d-1")
  expect(storage.getItem(checkpointKey("d-1"))).toBeNull()
})
