import { requestApi } from "./api"

export type ScoreBreakdown = {
  key: string
  label: string
  score: number
  maxScore: number
  reason: string
  missingEvidence: string[]
}

export type CareerRole = {
  roleName: string
  family: string
  description: string
  aliases: string[]
  requiredSkills: string[]
}

export type CareerRecommendation = {
  role: CareerRole
  tier: "stretch" | "stable" | "safe"
  totalScore: number
  matchingLevel: string
  scoreBreakdown: ScoreBreakdown[]
  matchingAdvantages: string[]
  missingSkills: string[]
  actionPlan: string[]
  alternatives: string[]
}

export type CareerRecommendationResponse = {
  profile: Record<string, unknown>
  generatedAt: string
  recommendationNotice: string
  tiers: Record<"stretch" | "stable" | "safe", CareerRecommendation[]>
}

export type CareerTaskRecord = {
  id: string
  planId: string
  title: string
  description: string
  dueDate: string | null
  status: string
  createdAt: string
  updatedAt: string
}

export type CareerTaskInput = {
  planId: string
  title: string
  description?: string
  dueDate?: string | null
  status?: string
}

export type CareerComparisonItem = {
  role: CareerRole
  totalScore: number
  matchingLevel: string
  scoreBreakdown: ScoreBreakdown[]
  matchingAdvantages: string[]
  missingSkills: string[]
  alternatives: string[]
  riskNotice: string
  actionPlan: { sevenDay: string[]; thirtyDay: string[]; ninetyDay: string[] }
}

export type CareerComparisonResponse = {
  profile: Record<string, unknown>
  items: CareerComparisonItem[]
  commonStrengths: string[]
  recommendationNotice: string
}

type BackendRole = {
  role_name: string
  family: string
  description: string
  aliases?: string[]
  required_skills?: string[]
  [key: string]: unknown
}

type BackendRecommendation = {
  role: BackendRole
  tier: CareerRecommendation["tier"]
  total_score: number
  matching_level: string
  score_breakdown: Array<{
    key: string
    label: string
    score: number
    max_score: number
    reason: string
    missing_evidence?: string[]
  }>
  matching_advantages: string[]
  missing_skills: string[]
  action_plan: string[]
  alternatives: string[]
}

type BackendTask = {
  id: string
  plan_id: string
  title: string
  description: string
  due_date: string | null
  status: string
  created_at: string
  updated_at: string
}

function fromRole(role: BackendRole): CareerRole {
  return {
    roleName: role.role_name || "",
    family: role.family || "",
    description: role.description || "",
    aliases: role.aliases || [],
    requiredSkills: role.required_skills || [],
  }
}

function fromScore(item: BackendRecommendation["score_breakdown"][number]): ScoreBreakdown {
  return {
    key: item.key,
    label: item.label,
    score: item.score,
    maxScore: item.max_score,
    reason: item.reason,
    missingEvidence: item.missing_evidence || [],
  }
}

function fromRecommendation(item: BackendRecommendation): CareerRecommendation {
  return {
    role: fromRole(item.role),
    tier: item.tier,
    totalScore: item.total_score || 0,
    matchingLevel: item.matching_level || "",
    scoreBreakdown: (item.score_breakdown || []).map(fromScore),
    matchingAdvantages: item.matching_advantages || [],
    missingSkills: item.missing_skills || [],
    actionPlan: item.action_plan || [],
    alternatives: item.alternatives || [],
  }
}

function fromTask(item: BackendTask): CareerTaskRecord {
  return {
    id: item.id,
    planId: item.plan_id,
    title: item.title,
    description: item.description,
    dueDate: item.due_date,
    status: item.status,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  }
}

export async function loadCareerRecommendations(): Promise<CareerRecommendationResponse> {
  const data = await requestApi<{
    profile: Record<string, unknown>
    generated_at: string
    recommendation_notice: string
    tiers: Record<"stretch" | "stable" | "safe", BackendRecommendation[]>
  }>("/api/career/recommend", { method: "POST", body: JSON.stringify({}) })
  return {
    profile: data.profile,
    generatedAt: data.generated_at,
    recommendationNotice: data.recommendation_notice,
    tiers: {
      stretch: (data.tiers.stretch || []).map(fromRecommendation),
      stable: (data.tiers.stable || []).map(fromRecommendation),
      safe: (data.tiers.safe || []).map(fromRecommendation),
    },
  }
}

export async function compareRoles(roleNames: string[]): Promise<CareerComparisonResponse> {
  const data = await requestApi<{
    profile: Record<string, unknown>
    items: Array<{
      role: BackendRole
      total_score: number
      matching_level: string
      score_breakdown: BackendRecommendation["score_breakdown"]
      matching_advantages: string[]
      missing_skills: string[]
      alternatives: string[]
      risk_notice: string
      action_plan: { seven_day: string[]; thirty_day: string[]; ninety_day: string[] }
    }>
    common_strengths: string[]
    recommendation_notice: string
  }>("/api/career/compare", {
    method: "POST",
    body: JSON.stringify({ role_names: roleNames }),
  })
  return {
    profile: data.profile,
    items: data.items.map((item) => ({
      role: fromRole(item.role),
      totalScore: item.total_score || 0,
      matchingLevel: item.matching_level || "",
      scoreBreakdown: (item.score_breakdown || []).map(fromScore),
      matchingAdvantages: item.matching_advantages || [],
      missingSkills: item.missing_skills || [],
      alternatives: item.alternatives || [],
      riskNotice: item.risk_notice || "",
      actionPlan: {
        sevenDay: item.action_plan?.seven_day || [],
        thirtyDay: item.action_plan?.thirty_day || [],
        ninetyDay: item.action_plan?.ninety_day || [],
      },
    })),
    commonStrengths: data.common_strengths,
    recommendationNotice: data.recommendation_notice,
  }
}

export async function listCareerTasks(planId: string): Promise<CareerTaskRecord[]> {
  const data = await requestApi<{ items: BackendTask[] }>("/api/career/tasks?plan_id=" + encodeURIComponent(planId))
  return data.items.map(fromTask)
}

export async function saveCareerTask(input: CareerTaskInput): Promise<CareerTaskRecord> {
  return fromTask(await requestApi<BackendTask>("/api/career/tasks", {
    method: "POST",
    body: JSON.stringify({
      plan_id: input.planId,
      title: input.title,
      description: input.description || "",
      due_date: input.dueDate || null,
      status: input.status || "pending",
    }),
  }))
}

export async function updateCareerTask(taskId: string, input: Partial<Pick<CareerTaskInput, "title" | "description" | "dueDate" | "status">>): Promise<CareerTaskRecord> {
  return fromTask(await requestApi<BackendTask>("/api/career/tasks/" + encodeURIComponent(taskId), {
    method: "PATCH",
    body: JSON.stringify({
      ...(input.title === undefined ? {} : { title: input.title }),
      ...(input.description === undefined ? {} : { description: input.description }),
      ...(input.dueDate === undefined ? {} : { due_date: input.dueDate }),
      ...(input.status === undefined ? {} : { status: input.status }),
    }),
  }))
}

export async function deleteCareerTask(taskId: string): Promise<void> {
  await requestApi<{ id: string }>("/api/career/tasks/" + encodeURIComponent(taskId), { method: "DELETE" })
}
