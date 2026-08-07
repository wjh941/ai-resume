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
  marketNotice: string
}

export interface ResumeReview {
  identityCode: IdentityCode
  identityLabel: string
  issues: string[]
  rewriteExamples: string[]
  keywords: string[]
  optimizedResumeText: string
  interviewIntro: string
}

export type AdviceTopic =
  | "simulation_interview"
  | "salary_negotiation"
  | "contract_pitfalls"
  | "career_planning"
  | "certificate_recommendation"
  | "role_comparison"
  | "written_test"
  | "job_channels"
  | "scam_screening"

export interface CareerAdvice {
  identityCode: IdentityCode
  identityLabel: string
  topic: AdviceTopic
  title: string
  sections: ConsultationSection[]
}
