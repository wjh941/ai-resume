import { describe, expect, it } from "vitest"

import { applyEvidenceSuggestion } from "../utils/evidence-suggestions"
import { createEmptyDraft } from "../types/resume"
import type { EvidenceSuggestion } from "../types/evidence"


const projectSuggestion: EvidenceSuggestion = {
  sourceEvidenceId: "evidence-1",
  sourceTitle: "Data pipeline",
  targetSection: "project",
  title: "Data pipeline",
  role: "Data Engineer related experience",
  description: "Action: built validation",
  riskNote: "",
}


describe("applyEvidenceSuggestion", () => {
  it("adds a project suggestion only to an empty target section", () => {
    const draft = createEmptyDraft()

    expect(applyEvidenceSuggestion(draft, projectSuggestion)).toBe(true)
    expect(draft.resume.projects).toEqual([{
      name: "Data pipeline",
      role: "Data Engineer related experience",
      startDate: "[待确认]",
      endDate: "[待确认]",
      description: "Action: built validation",
    }])

    expect(applyEvidenceSuggestion(draft, projectSuggestion)).toBe(false)
    expect(draft.resume.projects).toHaveLength(1)
  })

  it("does not alter existing employment when applying an employment suggestion", () => {
    const draft = createEmptyDraft()
    draft.resume.employment.push({
      company: "Existing company",
      position: "Existing role",
      startDate: "2025-01",
      endDate: "2025-06",
      description: "Existing user-authored experience",
    })
    const suggestion: EvidenceSuggestion = {
      ...projectSuggestion,
      targetSection: "employment",
    }

    expect(applyEvidenceSuggestion(draft, suggestion)).toBe(false)
    expect(draft.resume.employment).toHaveLength(1)
    expect(draft.resume.employment[0].company).toBe("Existing company")
  })
})
