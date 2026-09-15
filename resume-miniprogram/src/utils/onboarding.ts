import { getUniStorage } from "./persistence"

const ONBOARDING_KEY_PREFIX = "resume_demo_onboarding_v1"

function storageKey(userId: string): string {
  return `${ONBOARDING_KEY_PREFIX}:${userId}`
}

export function hasCompletedOnboarding(userId: string): boolean {
  return getUniStorage()?.getStorageSync(storageKey(userId)) === true
}

export function completeOnboarding(userId: string): void {
  getUniStorage()?.setStorageSync(storageKey(userId), true)
}
