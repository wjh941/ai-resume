const ONBOARDING_KEY_PREFIX = "resume_demo_onboarding_v1"

type UniStorage = {
  getStorageSync(key: string): unknown
  setStorageSync(key: string, value: unknown): void
}

function storage(): UniStorage | null {
  const candidate = (globalThis as typeof globalThis & { uni?: UniStorage }).uni
  return candidate
    && typeof candidate.getStorageSync === "function"
    && typeof candidate.setStorageSync === "function"
    ? candidate
    : null
}

function storageKey(userId: string): string {
  return `${ONBOARDING_KEY_PREFIX}:${userId}`
}

export function hasCompletedOnboarding(userId: string): boolean {
  return storage()?.getStorageSync(storageKey(userId)) === true
}

export function completeOnboarding(userId: string): void {
  storage()?.setStorageSync(storageKey(userId), true)
}
