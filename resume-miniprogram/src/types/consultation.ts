import type { JobIntelligence } from "./resume"

export type IdentityCode = "1" | "2" | "3" | "4" | "5"
export type ConsultationStage = "role-entry" | "identity-selection" | "job-analysis"

export interface ConsultationSection {
  order: number
  title: string
  items: string[]
}

export interface IdentityPlan {
  title: string
  sections: ConsultationSection[]
}

export interface JobConsultation {
  identityCode: IdentityCode
  identityLabel: string
  jobIntelligence: JobIntelligence
  jobAnalysisSections: ConsultationSection[]
  identityPlan: IdentityPlan
  followUpQuestion: string
}

export interface ResumeReview {
  identityCode: IdentityCode
  identityLabel: string
  issues: string[]
  rewriteExamples: string[]
  keywords: string[]
}
