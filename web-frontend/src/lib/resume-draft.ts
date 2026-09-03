import type { DraftSaveInput, TemplateId } from "./drafts"

export function createEmptyDraftInput(jobTitle: string, templateId: TemplateId): DraftSaveInput {
  const normalizedTitle = jobTitle.trim()
  return {
    id: "",
    jobTitle: normalizedTitle || "未命名简历",
    templateId,
    jobIntelligence: null,
    resume: {
      version: 1,
      basic: { name: "", phone: "", email: "", city: "" },
      job: { targetRole: normalizedTitle, expectedSalary: "", employmentType: "" },
      education: [],
      employment: [],
      projects: [],
      skills: { skills: [], certificates: [] },
      selfEvaluation: "",
      sectionVisibility: {
        basic: true,
        job: true,
        education: true,
        employment: true,
        projects: true,
        skills: true,
        selfEvaluation: true,
      },
    },
  }
}
