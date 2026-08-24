import { requestApi } from "./api"

export type AssessmentQuestion = {
  key: string
  group: "interest" | "work_style" | "strength_evidence" | "constraints"
  dimension: string
  title: string
}

export type AssessmentQuestionSet = {
  items: AssessmentQuestion[]
  notice: string
}

export type AssessmentReport = {
  topInterests: Array<{ key: string; label: string; score: number; reason: string }>
  workStyleSummary: string
  strengthEvidence: string[]
  confidenceNote: string
  answeredCount: number
  actionPlan: { sevenDay: string[]; thirtyDay: string[]; ninetyDay: string[] }
  reportScope?: string
  upgradeNotice?: string
  report?: {
    mode?: string
    summary?: string
    actions?: string[]
    evidence?: Array<Record<string, unknown>>
    source_notice?: string
    upgrade_notice?: string
  }
}

export type SavedAssessment = {
  clientId: string
  version: number
  answers: Record<string, number>
  result: AssessmentReport
  updatedAt: string
}

type BackendQuestion = AssessmentQuestion
type BackendResult = {
  top_interests?: AssessmentReport["topInterests"]
  work_style_summary?: string
  strength_evidence?: string[]
  confidence_note?: string
  answered_count?: number
  action_plan?: { seven_day?: string[]; thirty_day?: string[]; ninety_day?: string[] }
  report_scope?: string
  upgrade_notice?: string
  report?: AssessmentReport["report"]
}
type BackendAssessment = {
  client_id: string
  version: number
  answers: Record<string, number>
  result: BackendResult
  updated_at: string
}

function fromResult(result: BackendResult): AssessmentReport {
  return {
    topInterests: result.top_interests || [],
    workStyleSummary: result.work_style_summary || "",
    strengthEvidence: result.strength_evidence || [],
    confidenceNote: result.confidence_note || "",
    answeredCount: result.answered_count || 0,
    actionPlan: {
      sevenDay: result.action_plan?.seven_day || [],
      thirtyDay: result.action_plan?.thirty_day || [],
      ninetyDay: result.action_plan?.ninety_day || [],
    },
    reportScope: result.report_scope,
    upgradeNotice: result.upgrade_notice,
    report: result.report,
  }
}

function fromBackend(item: BackendAssessment): SavedAssessment {
  return {
    clientId: item.client_id,
    version: item.version,
    answers: item.answers,
    result: fromResult(item.result),
    updatedAt: item.updated_at,
  }
}

export async function getAssessmentQuestions(): Promise<AssessmentQuestionSet> {
  return requestApi<AssessmentQuestionSet>("/api/career/assessment/questions")
}

export async function loadAssessment(): Promise<SavedAssessment> {
  return fromBackend(await requestApi<BackendAssessment>("/api/career/assessment"))
}

export async function submitAssessment(
  answers: Record<string, number>,
  reportMode: "simplified" | "professional",
): Promise<SavedAssessment> {
  return fromBackend(await requestApi<BackendAssessment>("/api/career/assessment/submit", {
    method: "POST",
    body: JSON.stringify({ answers, report_mode: reportMode }),
  }))
}
