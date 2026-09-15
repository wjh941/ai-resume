const workspaceRecoveryPrefix = "workspace-recovery"

function workspaceKey(userId: string, feature: string): string {
  return `${workspaceRecoveryPrefix}:${userId}:${feature}`
}

/** 供 session-snapshot 等按 key 读写的调用方构造统一的工作区快照 key；userId 为空时返回空串（视为禁用）。 */
export function workspaceSnapshotKey(userId: string, feature: string): string {
  return userId ? workspaceKey(userId, feature) : ""
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
