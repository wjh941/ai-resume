import type { ResumeDraft } from "../types/resume"
import type { EvidenceSuggestion } from "../types/evidence"


const PENDING = "[待确认]"


export function applyEvidenceSuggestion(
  draft: ResumeDraft,
  suggestion: EvidenceSuggestion,
): boolean {
  if (suggestion.targetSection === "project") {
    if (draft.resume.projects.length > 0) return false
    draft.resume.projects.push({
      name: suggestion.title,
      role: suggestion.role,
      startDate: PENDING,
      endDate: PENDING,
      description: suggestion.description,
    })
    return true
  }

  if (draft.resume.employment.length > 0) return false
  draft.resume.employment.push({
    company: PENDING,
    position: suggestion.role,
    startDate: PENDING,
    endDate: PENDING,
    description: suggestion.description,
  })
  return true
}
