export function withReportMode(payload, mode) {
  return mode === "simplified" || mode === "professional"
    ? { ...payload, report_mode: mode }
    : { ...payload }
}

export function normalizeReport(result) {
  const report = result?.report || {}
  return {
    mode: report.mode === "professional" ? "professional" : "simplified",
    summary: typeof report.summary === "string" ? report.summary : "",
    actions: Array.isArray(report.actions) ? report.actions : [],
    evidence: Array.isArray(report.evidence) ? report.evidence : [],
    sourceNotice: typeof report.source_notice === "string" ? report.source_notice : "",
    upgradeNotice: typeof report.upgrade_notice === "string" ? report.upgrade_notice : "",
  }
}

export function visibleEvidence(report) {
  return report.mode === "professional" ? report.evidence : []
}

export function escapeText(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[character]))
}

if (typeof window !== "undefined") {
  window.ResumeDashboardReportTier = { withReportMode, normalizeReport, visibleEvidence, escapeText }
}
