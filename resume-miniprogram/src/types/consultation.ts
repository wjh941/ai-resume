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

export interface CareerGrowthStage {
  stage: string
  roleName: string
  yearsReference: string
  coreSkills: string[]
  responsibilities: string[]
  assessmentCriteria: string[]
}

export interface CareerGrowthRoute {
  title: string
  stages: CareerGrowthStage[]
}

export interface PrioritySkillGap {
  skillName: string
  learningDirection: string
  projectPractice: string
  practiceTask: string
}

export interface JobMatchReport {
  score: number
  scoreBasis: string[]
  matchingAdvantages: string[]
  missingSkills: string[]
  priorityGaps: PrioritySkillGap[]
}

export interface JobConsultation {
  identityCode: IdentityCode
  identityLabel: string
  jobIntelligence: JobIntelligence
  jobAnalysisSections: ConsultationSection[]
  identityPlan: IdentityPlan
  followUpQuestion: string
  marketNotice: string
  careerGrowthRoute: CareerGrowthRoute
  customRequirementNotes: string[]
}

export interface ResumeReview {
  identityCode: IdentityCode
  identityLabel: string
  issues: string[]
  rewriteExamples: string[]
  keywords: string[]
  optimizedResumeText: string
  interviewIntro: string
  jobMatchReport: JobMatchReport
  customRequirementNotes: string[]
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
