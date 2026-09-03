export type ReportMode = "simplified" | "professional"
export type JobsQuerySnapshot = { roleName: string; reportMode: ReportMode }
export type InsightsQuerySnapshot = { roleName: string; year: string; reportMode: ReportMode }

function isReportMode(value: unknown): value is ReportMode {
  return value === "simplified" || value === "professional"
}

export function validateJobsQuerySnapshot(value: unknown): Partial<JobsQuerySnapshot> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {}
  const candidate = value as Record<string, unknown>
  const snapshot: Partial<JobsQuerySnapshot> = {}
  if (typeof candidate.roleName === "string") snapshot.roleName = candidate.roleName
  if (isReportMode(candidate.reportMode)) snapshot.reportMode = candidate.reportMode
  return snapshot
}

export function validateInsightsQuerySnapshot(value: unknown): Partial<InsightsQuerySnapshot> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {}
  const candidate = value as Record<string, unknown>
  const snapshot: Partial<InsightsQuerySnapshot> = {}
  if (typeof candidate.roleName === "string") snapshot.roleName = candidate.roleName
  if (typeof candidate.year === "string" && /^\d{4}$/.test(candidate.year) && Number(candidate.year) >= 2000 && Number(candidate.year) <= 2100) snapshot.year = candidate.year
  if (isReportMode(candidate.reportMode)) snapshot.reportMode = candidate.reportMode
  return snapshot
}
