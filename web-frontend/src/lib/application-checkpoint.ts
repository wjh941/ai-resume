import type { ApplicationFormSnapshot } from "./application-form-state"

export type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem">

type Envelope = { version: 1; savedAt: number; snapshot: ApplicationFormSnapshot }

const CHECKPOINT_KEY = "resume_web_applications_checkpoint"
const FORM_FIELDS = ["company", "roleName", "city", "status", "source", "appliedAt", "nextActionAt", "nextInterviewAt", "interviewNotes", "notes", "contactInfo", "attachmentRef", "draftId"] as const
const TIMELINE_FIELDS = ["title", "description", "occurredAt"] as const

export type ApplicationCheckpoint = ApplicationFormSnapshot & { savedAt: number }

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function hasStringFields(value: unknown, fields: readonly string[]): boolean {
  return isRecord(value) && fields.every((field) => typeof value[field] === "string")
}

function isValidSnapshot(value: unknown): value is ApplicationFormSnapshot {
  if (!isRecord(value)) return false
  return typeof value.reminderAt === "string"
    && hasStringFields(value.form, FORM_FIELDS)
    && hasStringFields(value.timeline, TIMELINE_FIELDS)
}

/** 表单变动时写入本地检查点（仅本地，服务端记录不受影响）。 */
export function writeApplicationCheckpoint(storage: StorageLike, snapshot: ApplicationFormSnapshot, savedAt = Date.now()): void {
  const envelope: Envelope = { version: 1, savedAt, snapshot }
  storage.setItem(CHECKPOINT_KEY, JSON.stringify(envelope))
}

/** 读取本机检查点；格式不符或损坏时返回 null（与 draft-checkpoint 同样的防御式解析）。 */
export function readApplicationCheckpoint(storage: StorageLike): ApplicationCheckpoint | null {
  try {
    const raw = storage.getItem(CHECKPOINT_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<Envelope>
    if (parsed.version !== 1 || !Number.isFinite(parsed.savedAt) || !isValidSnapshot(parsed.snapshot)) return null
    return { ...(parsed.snapshot as ApplicationFormSnapshot), savedAt: parsed.savedAt! }
  } catch {
    return null
  }
}

/** 表单提交成功或用户放弃时清除检查点。 */
export function clearApplicationCheckpoint(storage: StorageLike): void {
  storage.removeItem(CHECKPOINT_KEY)
}
