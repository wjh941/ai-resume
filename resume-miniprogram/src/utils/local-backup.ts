import type {
  CareerProfilePayload,
  CareerRecommendationResult,
  RecommendationTier,
  RoleRecommendation,
  WeeklyCareerTarget,
} from "../types/career"
import type { JobIntelligence, ResumeDraft } from "../types/resume"

export type ResumeBackupState = {
  activeJob: JobIntelligence | null
  draft: ResumeDraft
}

export type CareerBackupState = {
  profile: CareerProfilePayload | null
  result: CareerRecommendationResult | null
  selectedTier: RecommendationTier
  selectedRole: RoleRecommendation | null
  comparisonRoleNames: string[]
  weeklyTarget: WeeklyCareerTarget | null
}

export type LocalBackup = {
  version: 1
  exportedAt: string
  resume: ResumeBackupState
  career: CareerBackupState
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

export function serializeLocalBackup(resume: ResumeBackupState, career: CareerBackupState): string {
  const backup: LocalBackup = {
    version: 1,
    exportedAt: new Date().toISOString(),
    resume: clone(resume),
    career: clone(career),
  }
  return JSON.stringify(backup, null, 2)
}

export function parseLocalBackup(source: string): LocalBackup {
  let parsed: unknown
  try {
    parsed = JSON.parse(source)
  } catch {
    throw new Error("The backup file is invalid or unsupported.")
  }
  if (!isRecord(parsed) || parsed.version !== 1 || !isRecord(parsed.resume) || !isRecord(parsed.career)) {
    throw new Error("The backup file is invalid or unsupported.")
  }
  if (!isRecord(parsed.resume.draft) || !isRecord(parsed.resume.draft.resume)) {
    throw new Error("The backup file is invalid or unsupported.")
  }
  return clone(parsed as LocalBackup)
}
