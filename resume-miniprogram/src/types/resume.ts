export type TemplateId = "business" | "technology" | "graduate" | "analytics"

export interface JobIntelligence {
  version: 1
  roleName: string
  salaryByExperience: Record<string, string>
  responsibilities: string[]
  hardRequirements: string[]
  requiredSkills: string[]
  bonusSkills: string[]
  careerRoute: string[]
}

export interface ResumePayload {
  version: 1
  basic: { name: string; phone: string; email: string; city: string; gender: string }
  job: { targetRole: string; expectedSalary: string; availability: string }
  education: Array<{ school: string; major: string; degree: string; startDate: string; endDate: string; courses: string }>
  employment: Array<{ company: string; position: string; startDate: string; endDate: string; description: string }>
  projects: Array<{ name: string; role: string; startDate: string; endDate: string; description: string }>
  skills: { skills: string[]; certificates: string[]; englishLevel: string }
  selfEvaluation: string
  sectionVisibility: {
    basic: boolean; job: boolean; education: boolean; employment: boolean
    projects: boolean; skills: boolean; selfEvaluation: boolean
  }
}

export interface ResumeDraft {
  id?: string
  jobTitle: string
  templateId: TemplateId
  resume: ResumePayload
  jobIntelligence: JobIntelligence | null
}

export function createEmptyResume(): ResumePayload {
  return {
    version: 1,
    basic: { name: "", phone: "", email: "", city: "", gender: "" },
    job: { targetRole: "", expectedSalary: "", availability: "" },
    education: [],
    employment: [],
    projects: [],
    skills: { skills: [], certificates: [], englishLevel: "" },
    selfEvaluation: "",
    sectionVisibility: {
      basic: true, job: true, education: true, employment: true,
      projects: true, skills: true, selfEvaluation: true,
    },
  }
}

export function createEmptyDraft(): ResumeDraft {
  return {
    jobTitle: "",
    templateId: "business",
    resume: createEmptyResume(),
    jobIntelligence: null,
  }
}
