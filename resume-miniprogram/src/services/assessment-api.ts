import { request } from "./http"
import type {
  AnnualInsight,
  AssessmentQuestion,
  AssessmentQuestionSet,
  AssessmentResult,
  SavedAssessment,
} from "../types/assessment"

type BackendQuestion = {
  key: string
  group: AssessmentQuestion["group"]
  dimension: string
  title: string
}

type BackendResult = {
  top_interests: Array<{
    key: string
    label: string
    score: number
    reason: string
  }>
  work_style_summary: string
  strength_evidence: string[]
  confidence_note: string
  answered_count: number
  action_plan: {
    seven_day: string[]
    thirty_day: string[]
    ninety_day: string[]
  }
}

type BackendSavedAssessment = {
  client_id: string
  version: number
  answers: Record<string, number>
  result: BackendResult
  updated_at: string
}

type BackendAnnualInsight = {
  id: number
  year: number
  scope: string
  audience: string
  category: string
  title: string
  content: string
  source_label: string
  publication_date: string
  confidence_note: string
  created_at: string
}

function fromResult(result: BackendResult): AssessmentResult {
  return {
    topInterests: result.top_interests,
    workStyleSummary: result.work_style_summary,
    strengthEvidence: result.strength_evidence,
    confidenceNote: result.confidence_note,
    answeredCount: result.answered_count,
    actionPlan: {
      sevenDay: result.action_plan.seven_day,
      thirtyDay: result.action_plan.thirty_day,
      ninetyDay: result.action_plan.ninety_day,
    },
  }
}

function fromSavedAssessment(item: BackendSavedAssessment): SavedAssessment {
  return {
    clientId: item.client_id,
    version: item.version,
    answers: item.answers,
    result: fromResult(item.result),
    updatedAt: item.updated_at,
  }
}

function fromAnnualInsight(item: BackendAnnualInsight): AnnualInsight {
  return {
    id: item.id,
    year: item.year,
    scope: item.scope,
    audience: item.audience,
    category: item.category,
    title: item.title,
    content: item.content,
    sourceLabel: item.source_label,
    publicationDate: item.publication_date,
    confidenceNote: item.confidence_note,
    createdAt: item.created_at,
  }
}

export async function getAssessmentQuestions(): Promise<AssessmentQuestionSet> {
  const data = await request<{ items: BackendQuestion[]; notice: string }>(
    "/api/career/assessment/questions",
  )
  return { items: data.items, notice: data.notice }
}

export async function submitAssessment(
  clientId: string,
  answers: Record<string, number>,
): Promise<SavedAssessment> {
  const data = await request<BackendSavedAssessment>(
    "/api/career/assessment/submit",
    "POST",
    { client_id: clientId, answers },
  )
  return fromSavedAssessment(data)
}

export async function loadAssessment(clientId: string): Promise<SavedAssessment> {
  return fromSavedAssessment(
    await request<BackendSavedAssessment>("/api/career/assessment", "GET", undefined, { query: { client_id: clientId } }),
  )
}

export async function loadAssessmentData(clientId: string): Promise<{
  questions: AssessmentQuestionSet
  insights: AnnualInsight[]
  saved: SavedAssessment | null
}> {
  const questions = await getAssessmentQuestions()
  const [insights, saved] = await Promise.all([
    listAnnualInsights().catch(() => []),
    loadAssessment(clientId).catch(() => null),
  ])
  return { questions, insights, saved }
}

export async function listAnnualInsights(year?: number): Promise<AnnualInsight[]> {
  const data = await request<{ items: BackendAnnualInsight[] }>(
    "/api/career/annual-insights",
    "GET",
    undefined,
    { query: { year: year ? String(year) : undefined } },
  )
  return data.items.map(fromAnnualInsight)
}
