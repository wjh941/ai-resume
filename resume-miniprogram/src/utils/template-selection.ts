import type { ResumeReadinessReport } from "../types/evidence"

export function decideTemplateSelection(report: ResumeReadinessReport): {
  blocked: boolean
  requiresWarningConfirmation: boolean
} {
  const blocked = report.blockingItems.length > 0
  return {
    blocked,
    requiresWarningConfirmation: !blocked && report.warningItems.length > 0,
  }
}
