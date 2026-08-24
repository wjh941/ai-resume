import type { DraftRecord } from "./drafts"

export type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem">
type Envelope = { version: 1; draftId: string; savedAt: number; draft: DraftRecord }

const TEMPLATE_IDS = new Set(["business", "technology", "graduate", "analytics"])
const VISIBILITY_KEYS = ["basic", "job", "education", "employment", "projects", "skills"] as const

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function hasStringFields(value: unknown, fields: readonly string[]): boolean {
  return isRecord(value) && fields.every((field) => typeof value[field] === "string")
}

function hasStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string")
}

function hasRecordArray(value: unknown, fields: readonly string[]): boolean {
  return Array.isArray(value) && value.every((item) => hasStringFields(item, fields))
}

function isDraftRecord(value: unknown, draftId: string): value is DraftRecord {
  if (!isRecord(value) || value.id !== draftId || typeof value.jobTitle !== "string") return false
  if (typeof value.templateId !== "string" || !TEMPLATE_IDS.has(value.templateId)) return false
  if (typeof value.createdAt !== "string" || typeof value.updatedAt !== "string") return false
  if (value.jobIntelligence !== null && !isRecord(value.jobIntelligence)) return false
  if (!isRecord(value.resume) || value.resume.version !== 1) return false

  const resume = value.resume
  if (!hasStringFields(resume.basic, ["name", "phone", "email", "city"])) return false
  if (!hasStringFields(resume.job, ["targetRole", "expectedSalary", "employmentType"])) return false
  if (!hasRecordArray(resume.education, ["school", "major", "degree", "startDate", "endDate"])) return false
  if (!hasRecordArray(resume.employment, ["company", "position", "startDate", "endDate", "description"])) return false
  if (!hasRecordArray(resume.projects, ["name", "role", "startDate", "endDate", "description"])) return false
  if (!isRecord(resume.skills) || !hasStringArray(resume.skills.skills) || !hasStringArray(resume.skills.certificates)) return false
  if (typeof resume.selfEvaluation !== "string" || !isRecord(resume.sectionVisibility)) return false
  const visibility = resume.sectionVisibility
  const hasSelfEvaluation = typeof visibility.selfEvaluation === "boolean"
    || typeof visibility.self_evaluation === "boolean"
  return hasSelfEvaluation && VISIBILITY_KEYS.every((key) => typeof visibility[key] === "boolean")
}

export const checkpointKey = (draftId: string) => `resume_web_checkpoint:${draftId}`

export function writeDraftCheckpoint(storage: StorageLike, draft: DraftRecord, savedAt = Date.now()): void {
  const envelope: Envelope = { version: 1, draftId: draft.id, savedAt, draft }
  storage.setItem(checkpointKey(draft.id), JSON.stringify(envelope))
}

export function readDraftCheckpoint(
  storage: StorageLike,
  draftId: string,
  serverUpdatedAt: string,
): DraftRecord | null {
  try {
    const raw = storage.getItem(checkpointKey(draftId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<Envelope>
    const serverTime = Date.parse(serverUpdatedAt)
    if (parsed.version !== 1 || parsed.draftId !== draftId || !Number.isFinite(parsed.savedAt)) return null
    if (Number.isFinite(serverTime) && parsed.savedAt! <= serverTime) return null
    if (!isDraftRecord(parsed.draft, draftId)) return null
    return parsed.draft
  } catch {
    return null
  }
}

export function clearDraftCheckpoint(storage: StorageLike, draftId: string): void {
  storage.removeItem(checkpointKey(draftId))
}
