export type AssessmentQuestionGroup =
  | "interest"
  | "work_style"
  | "strength_evidence"
  | "constraints"

export type AssessmentQuestion = {
  key: string
  group: AssessmentQuestionGroup
  dimension: string
  title: string
}

export type AssessmentQuestionSet = {
  items: AssessmentQuestion[]
  notice: string
}

export type AssessmentInterest = {
  key: string
  label: string
  score: number
  reason: string
}

export type AssessmentActionPlan = {
  sevenDay: string[]
  thirtyDay: string[]
  ninetyDay: string[]
}

export type AssessmentResult = {
  topInterests: AssessmentInterest[]
  workStyleSummary: string
  strengthEvidence: string[]
  confidenceNote: string
  answeredCount: number
  actionPlan: AssessmentActionPlan
}

export type SavedAssessment = {
  clientId: string
  version: number
  answers: Record<string, number>
  result: AssessmentResult
  updatedAt: string
}

export type AnnualInsight = {
  id: number
  year: number
  scope: string
  audience: string
  category: string
  title: string
  content: string
  sourceLabel: string
  publicationDate: string
  confidenceNote: string
  createdAt: string
}
