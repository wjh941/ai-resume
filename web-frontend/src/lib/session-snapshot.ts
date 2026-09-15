// sessionStorage 快照读写的统一入口。
// 环境不支持（SSR / 隐私模式抛错）时安全降级为 no-op / null，
// 取代各视图里重复的 `(() => { try { ... sessionStorage ... } catch { return null } })()` IIFE。
function safeSessionStorage(): Storage | null {
  try {
    return typeof sessionStorage === "undefined" ? null : sessionStorage
  } catch {
    return null
  }
}

export function readSessionSnapshot<T>(key: string): T | null {
  if (!key) return null
  const storage = safeSessionStorage()
  if (!storage) return null
  try {
    const raw = storage.getItem(key)
    return raw === null ? null : JSON.parse(raw) as T
  } catch {
    return null
  }
}

export function writeSessionSnapshot(key: string, value: unknown): void {
  if (!key) return
  const storage = safeSessionStorage()
  if (!storage) return
  try {
    storage.setItem(key, JSON.stringify(value))
  } catch {
    // 快照是可选的恢复能力：容量不足或存储被禁用时静默忽略。
  }
}

export function clearSessionSnapshot(key: string): void {
  if (!key) return
  const storage = safeSessionStorage()
  if (!storage) return
  try {
    storage.removeItem(key)
  } catch {
    // 同上：清除失败可安全忽略。
  }
}
