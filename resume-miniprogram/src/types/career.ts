export type CareerIdentityCode = "1" | "2" | "3" | "4" | "5"
export type RecommendationTier = "stretch" | "stable" | "safe"
export type MatchingLevel = "high" | "transferable" | "needs_upskilling" | "long_shot"

export type CareerProfilePayload = {
  clientId: string
  identityCode: CareerIdentityCode
  major: string
  educationLevel: string
  graduationYear: number | null
  cityPreferences: string[]
  minimumSalary: string
  industryPreferences: string[]
  workTypes: string[]
  skills: string[]
  draftId: string | null
}

export type CareerProfile = CareerProfilePayload & { updatedAt: string }

export type RoleSuggestion = {
  roleName: string
  family: string
  description: string
}

export type MajorSuggestion = {
  majorName: string
  category: string
  relatedFamilies: string[]
}

export type ScoreBreakdown = {
  key: string
  label: string
  score: number
  maxScore: number
  reason: string
  missingEvidence: string[]
}

export type RoleRecommendation = {
  role: {
    roleName: string
    family: string
    aliases: string[]
    recommendedMajors: string[]
    adjacentMajors: string[]
    relevantCourses: string[]
    requiredSkills: string[]
    entrySkills: string[]
    alternativeRoles: string[]
    internshipRoles: string[]
    entryDifficulty: number
    industryTags: string[]
    description: string
  }
  tier: RecommendationTier
  totalScore: number
  matchingLevel: MatchingLevel
  scoreBreakdown: ScoreBreakdown[]
  matchingAdvantages: string[]
  missingSkills: string[]
  actionPlan: string[]
  alternatives: string[]
}

export type CareerRecommendationResult = {
  profile: CareerProfile
  generatedAt: string
  recommendationNotice: string
  majorReport: {
    major: string
    matchingLevel: MatchingLevel
    matchingAdvantages: string[]
    missingSkills: string[]
    recommendedCourses: string[]
    recommendedProjects: string[]
    practiceTasks: string[]
  }
  tiers: Record<RecommendationTier, RoleRecommendation[]>
}
