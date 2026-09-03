const workspaceRecoveryPrefix = "workspace-recovery"

function workspaceKey(userId: string, feature: string): string {
  return `${workspaceRecoveryPrefix}:${userId}:${feature}`
}

export function readWorkspaceSnapshot<T>(storage: Storage, userId: string, feature: string): T | null {
  if (!userId) return null
  try {
    const value = storage.getItem(workspaceKey(userId, feature))
    return value === null ? null : JSON.parse(value) as T
  } catch { return null }
}

export function writeWorkspaceSnapshot<T>(storage: Storage, userId: string, feature: string, value: T): void {
  if (!userId) return
  try { storage.setItem(workspaceKey(userId, feature), JSON.stringify(value)) } catch { /* optional storage */ }
}

export function clearWorkspaceSnapshot(storage: Storage, userId: string, feature: string): void {
  if (!userId) return
  try { storage.removeItem(workspaceKey(userId, feature)) } catch { /* optional storage */ }
}
