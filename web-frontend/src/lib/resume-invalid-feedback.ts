const RESUME_FIELD_CONTROL_IDS: ReadonlyArray<readonly [string, string]> = [
  ["jobTitle", "resume-job-title"],
  ["basic.name", "resume-basic-name"],
  ["basic.phone", "resume-basic-phone"],
  ["basic.email", "resume-basic-email"],
  ["job.targetRole", "resume-target-role"],
]

type InvalidControl = {
  focus(options?: FocusOptions): void
  scrollIntoView(options?: ScrollIntoViewOptions): void
}

type InvalidFeedbackRoot = {
  getElementById(id: string): InvalidControl | null
}

export function resolveResumeInvalidSummary(
  active: boolean,
  errors: Record<string, string>,
): string {
  return active ? Object.values(errors)[0] || "" : ""
}

export function focusFirstInvalidResumeField(
  errors: Record<string, string>,
  root: InvalidFeedbackRoot = document,
): boolean {
  for (const [field, controlId] of RESUME_FIELD_CONTROL_IDS) {
    if (!errors[field]) continue
    const control = root.getElementById(controlId)
    if (!control) continue
    control.focus({ preventScroll: true })
    control.scrollIntoView({ block: "center", behavior: "smooth" })
    return true
  }
  return false
}
