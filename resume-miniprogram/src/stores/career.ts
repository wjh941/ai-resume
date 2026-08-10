import { defineStore } from "pinia"

import type {
  CareerProfilePayload,
  CareerRecommendationResult,
  RecommendationTier,
  RoleRecommendation,
} from "../types/career"

const CHECKPOINT_KEY = "resume_demo_career_planner"

type UniStorage = { getStorageSync(key: string): unknown; setStorageSync(key: string, value: unknown): void }
const storage = (): UniStorage | null => (globalThis as typeof globalThis & { uni?: UniStorage }).uni ?? null
const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T

export const useCareerStore = defineStore("career", {
  state: () => ({
    profile: null as CareerProfilePayload | null,
    result: null as CareerRecommendationResult | null,
    selectedTier: "stable" as RecommendationTier,
    selectedRole: null as RoleRecommendation | null,
  }),
  actions: {
    checkpoint(): void {
      storage()?.setStorageSync(CHECKPOINT_KEY, clone({
        profile: this.profile,
        selectedTier: this.selectedTier,
        selectedRole: this.selectedRole,
      }))
    },
    restoreCheckpoint(): void {
      const saved = storage()?.getStorageSync(CHECKPOINT_KEY) as Partial<typeof this.$state> | undefined
      if (!saved) return
      this.profile = saved.profile ?? null
      this.selectedTier = saved.selectedTier ?? "stable"
      this.selectedRole = saved.selectedRole ?? null
    },
    setProfile(profile: CareerProfilePayload): void {
      this.profile = clone(profile)
      this.checkpoint()
    },
    setResult(result: CareerRecommendationResult): void {
      this.result = clone(result)
      this.profile = {
        clientId: result.profile.clientId, identityCode: result.profile.identityCode,
        major: result.profile.major, educationLevel: result.profile.educationLevel,
        graduationYear: result.profile.graduationYear, cityPreferences: result.profile.cityPreferences,
        minimumSalary: result.profile.minimumSalary, industryPreferences: result.profile.industryPreferences,
        workTypes: result.profile.workTypes, skills: result.profile.skills, draftId: result.profile.draftId,
      }
      this.checkpoint()
    },
    selectRole(role: RoleRecommendation): void {
      this.selectedRole = clone(role)
      this.checkpoint()
    },
  },
})
