const LOCAL_CAREER_WORKSPACE_KEYS = [
  "resume_demo_checkpoint",
  "resume_demo_career_planner",
  "resume_demo_consultation",
  "resume_demo_assessment",
  "resume_demo_application_pending",
] as const

type UniStorage = {
  removeStorageSync(key: string): void
}

export function clearLocalCareerWorkspace(): void {
  const storage = (globalThis as typeof globalThis & { uni?: UniStorage }).uni
  if (!storage) return
  for (const key of LOCAL_CAREER_WORKSPACE_KEYS) storage.removeStorageSync(key)
}
