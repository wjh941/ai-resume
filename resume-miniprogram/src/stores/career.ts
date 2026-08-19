import { defineStore } from "pinia"

import type {
  CareerProfilePayload,
  CareerRecommendationResult,
  RecommendationTier,
  RoleRecommendation,
  WeeklyCareerTarget,
} from "../types/career"
import type { CareerBackupState } from "../utils/local-backup"

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
    comparisonRoleNames: [] as string[],
    weeklyTarget: null as WeeklyCareerTarget | null,
  }),
  actions: {
    checkpoint(): void {
      storage()?.setStorageSync(CHECKPOINT_KEY, clone({
        profile: this.profile,
        selectedTier: this.selectedTier,
        selectedRole: this.selectedRole,
        comparisonRoleNames: this.comparisonRoleNames,
        weeklyTarget: this.weeklyTarget,
      }))
    },
    restoreCheckpoint(): void {
      const saved = storage()?.getStorageSync(CHECKPOINT_KEY) as Partial<typeof this.$state> | undefined
      if (!saved) return
      this.profile = saved.profile ?? null
      this.selectedTier = saved.selectedTier ?? "stable"
      this.selectedRole = saved.selectedRole ?? null
      this.comparisonRoleNames = saved.comparisonRoleNames ?? []
      this.weeklyTarget = saved.weeklyTarget ?? null
    },
    exportBackup(): CareerBackupState {
      return clone({
        profile: this.profile,
        result: this.result,
        selectedTier: this.selectedTier,
        selectedRole: this.selectedRole,
        comparisonRoleNames: this.comparisonRoleNames,
        weeklyTarget: this.weeklyTarget,
      })
    },
    restoreBackup(snapshot: CareerBackupState): boolean {
      if (!snapshot || !Array.isArray(snapshot.comparisonRoleNames)) return false
      this.profile = clone(snapshot.profile ?? null)
      this.result = clone(snapshot.result ?? null)
      this.selectedTier = ["stretch", "stable", "safe"].includes(snapshot.selectedTier)
        ? snapshot.selectedTier
        : "stable"
      this.selectedRole = clone(snapshot.selectedRole ?? null)
      this.comparisonRoleNames = clone(snapshot.comparisonRoleNames.slice(0, 4))
      this.weeklyTarget = clone(snapshot.weeklyTarget ?? null)
      this.checkpoint()
      return true
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
    toggleComparisonRole(roleName: string): boolean {
      const index = this.comparisonRoleNames.indexOf(roleName)
      if (index >= 0) {
        this.comparisonRoleNames.splice(index, 1)
      } else if (this.comparisonRoleNames.length >= 4) {
        return false
      } else {
        this.comparisonRoleNames.push(roleName)
      }
      this.checkpoint()
      return true
    },
    setWeeklyTarget(role: {
      role: RoleRecommendation["role"]
      totalScore: number
      matchingLevel: WeeklyCareerTarget["matchingLevel"]
    }): void {
      this.weeklyTarget = {
        roleName: role.role.roleName,
        family: role.role.family,
        totalScore: role.totalScore,
        matchingLevel: role.matchingLevel,
      }
      this.checkpoint()
    },
    resetPlanner(checkpoint = true): void {
      this.profile = null
      this.result = null
      this.selectedTier = "stable"
      this.selectedRole = null
      this.comparisonRoleNames = []
      this.weeklyTarget = null
      if (checkpoint) this.checkpoint()
    },
  },
})
