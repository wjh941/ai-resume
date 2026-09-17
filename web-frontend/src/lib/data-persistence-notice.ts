export const PERSISTENCE_NOTICE_KEY = "resume-persistence-notice-dismissed-at"
export const PERSISTENCE_NOTICE_INTERVAL_MS = 7 * 24 * 60 * 60 * 1000

type StorageLike = Pick<Storage, "getItem" | "setItem">

/**
 * 免费托管的数据库不长期持久（服务重启可能清空）——用一条可关闭的提示
 * 引导用户定期导出备份；关闭后 7 天内不再打扰。
 */
export function shouldShowPersistenceNotice(storage: StorageLike, now: Date = new Date()): boolean {
  let dismissedAt = Number.NaN
  try {
    dismissedAt = Number(storage.getItem(PERSISTENCE_NOTICE_KEY))
  } catch {
    return true
  }
  if (!Number.isFinite(dismissedAt)) return true
  return now.getTime() - dismissedAt >= PERSISTENCE_NOTICE_INTERVAL_MS
}

export function markPersistenceNoticeDismissed(storage: StorageLike, now: Date = new Date()): void {
  try {
    storage.setItem(PERSISTENCE_NOTICE_KEY, String(now.getTime()))
  } catch {
    // 存储不可用时静默：下次进入仍会提示。
  }
}
