import { request } from "./http"
import type {
  CareerProfile,
  CareerProfilePayload,
  CareerComparisonItem,
  CareerComparisonResult,
  CareerRecommendationResult,
  MajorSuggestion,
  RoleRecommendation,
  RoleSuggestion,
} from "../types/career"

type BackendProfile = {
  client_id: string; identity_code: CareerProfile["identityCode"]; major: string
  education_level: string; graduation_year: number | null; city_preferences: string[]
  minimum_salary: string | null; industry_preferences: string[]; work_types: string[]
  skills: string[]; draft_id: string | null; updated_at: string
}

const fromProfile = (profile: BackendProfile): CareerProfile => ({
  clientId: profile.client_id,
  identityCode: profile.identity_code,
  major: profile.major,
  educationLevel: profile.education_level,
  graduationYear: profile.graduation_year,
  cityPreferences: profile.city_preferences,
  minimumSalary: profile.minimum_salary || "",
  industryPreferences: profile.industry_preferences,
  workTypes: profile.work_types,
  skills: profile.skills,
  draftId: profile.draft_id,
  updatedAt: profile.updated_at,
})

const toProfile = (profile: CareerProfilePayload) => ({
  client_id: profile.clientId,
  identity_code: profile.identityCode,
  major: profile.major,
  education_level: profile.educationLevel,
  graduation_year: profile.graduationYear,
  city_preferences: profile.cityPreferences,
  minimum_salary: profile.minimumSalary || undefined,
  industry_preferences: profile.industryPreferences,
  work_types: profile.workTypes,
  skills: profile.skills,
  draft_id: profile.draftId || undefined,
})

const mapRole = (role: Record<string, unknown>): RoleRecommendation["role"] => ({
  roleName: role.role_name as string, family: role.family as string, aliases: role.aliases as string[],
  recommendedMajors: role.recommended_majors as string[], adjacentMajors: role.adjacent_majors as string[],
  relevantCourses: role.relevant_courses as string[], requiredSkills: role.required_skills as string[],
  entrySkills: role.entry_skills as string[], alternativeRoles: role.alternative_roles as string[],
  internshipRoles: role.internship_roles as string[], entryDifficulty: role.entry_difficulty as number,
  industryTags: role.industry_tags as string[], description: role.description as string,
})

const mapScoreBreakdown = (items: Array<Record<string, unknown>>) => items.map((score) => ({
  key: score.key as string, label: score.label as string, score: score.score as number,
  maxScore: score.max_score as number, reason: score.reason as string,
  missingEvidence: score.missing_evidence as string[],
}))

export async function queryRoleSuggestions(query: string): Promise<RoleSuggestion[]> {
  const data = await request<{ items: Array<{ role_name: string; family: string; description: string }> }>(
    `/api/role/suggestions?q=${encodeURIComponent(query)}`,
  )
  return data.items.map((item) => ({
    roleName: item.role_name,
    family: item.family,
    description: item.description,
  }))
}

export async function queryMajorSuggestions(query: string): Promise<MajorSuggestion[]> {
  const data = await request<{ items: Array<{ major_name: string; category: string; related_families: string[] }> }>(
    `/api/major/suggestions?q=${encodeURIComponent(query)}`,
  )
  return data.items.map((item) => ({
    majorName: item.major_name,
    category: item.category,
    relatedFamilies: item.related_families,
  }))
}

export async function saveCareerProfile(profile: CareerProfilePayload): Promise<CareerProfile> {
  return fromProfile(await request<BackendProfile>("/api/career/profile/save", "POST", toProfile(profile)))
}

export async function loadCareerProfile(clientId: string): Promise<CareerProfile> {
  return fromProfile(await request<BackendProfile>(`/api/career/profile?client_id=${encodeURIComponent(clientId)}`))
}

export async function generateCareerRecommendations(clientId: string): Promise<CareerRecommendationResult> {
  const data = await request<{
    profile: BackendProfile
    generated_at: string
    recommendation_notice: string
    major_report: {
      major: string; matching_level: CareerRecommendationResult["majorReport"]["matchingLevel"]
      matching_advantages: string[]; missing_skills: string[]; recommended_courses: string[]
      recommended_projects: string[]; practice_tasks: string[]
    }
    tiers: Record<string, Array<Record<string, unknown>>>
  }>(`/api/career/recommend?client_id=${encodeURIComponent(clientId)}`, "POST")
  const mapRecommendation = (item: Record<string, unknown>) => {
    return {
      role: mapRole(item.role as Record<string, unknown>),
      tier: item.tier as "stretch" | "stable" | "safe",
      totalScore: item.total_score as number,
      matchingLevel: item.matching_level as RoleRecommendation["matchingLevel"],
      scoreBreakdown: mapScoreBreakdown(item.score_breakdown as Array<Record<string, unknown>>),
      matchingAdvantages: item.matching_advantages as string[],
      missingSkills: item.missing_skills as string[],
      actionPlan: item.action_plan as string[],
      alternatives: item.alternatives as string[],
    }
  }
  return {
    profile: fromProfile(data.profile),
    generatedAt: data.generated_at,
    recommendationNotice: data.recommendation_notice,
    majorReport: {
      major: data.major_report.major,
      matchingLevel: data.major_report.matching_level,
      matchingAdvantages: data.major_report.matching_advantages,
      missingSkills: data.major_report.missing_skills,
      recommendedCourses: data.major_report.recommended_courses,
      recommendedProjects: data.major_report.recommended_projects,
      practiceTasks: data.major_report.practice_tasks,
    },
    tiers: {
      stretch: data.tiers.stretch.map(mapRecommendation),
      stable: data.tiers.stable.map(mapRecommendation),
      safe: data.tiers.safe.map(mapRecommendation),
    },
  }
}

export async function compareRoles(
  clientId: string,
  roleNames: string[],
): Promise<CareerComparisonResult> {
  const data = await request<{
    profile: BackendProfile
    items: Array<Record<string, unknown>>
    common_strengths: string[]
    recommendation_notice: string
  }>("/api/career/compare", "POST", {
    client_id: clientId,
    role_names: roleNames,
  })
  const items: CareerComparisonItem[] = data.items.map((item) => ({
    role: mapRole(item.role as Record<string, unknown>),
    totalScore: item.total_score as number,
    matchingLevel: item.matching_level as CareerComparisonItem["matchingLevel"],
    scoreBreakdown: mapScoreBreakdown(item.score_breakdown as Array<Record<string, unknown>>),
    matchingAdvantages: item.matching_advantages as string[],
    missingSkills: item.missing_skills as string[],
    alternatives: item.alternatives as string[],
    riskNotice: item.risk_notice as string,
    actionPlan: {
      sevenDay: (item.action_plan as Record<string, string[]>).seven_day,
      thirtyDay: (item.action_plan as Record<string, string[]>).thirty_day,
      ninetyDay: (item.action_plan as Record<string, string[]>).ninety_day,
    },
  }))
  return {
    profile: fromProfile(data.profile),
    items,
    commonStrengths: data.common_strengths,
    recommendationNotice: data.recommendation_notice,
  }
}
