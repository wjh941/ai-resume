/** uni 双端本地存储的统一访问入口：所有 store/工具共用，避免各自重复定义。 */
export type UniStorage = {
  getStorageSync(key: string): unknown
  setStorageSync(key: string, value: unknown): void
  removeStorageSync?(key: string): void
}

export function getUniStorage(): UniStorage | null {
  const candidate = (globalThis as typeof globalThis & { uni?: UniStorage }).uni
  return candidate
    && typeof candidate.getStorageSync === "function"
    && typeof candidate.setStorageSync === "function"
    ? candidate
    : null
}

/** 结构化克隆的保守实现：checkpoint/backup 需要脱离响应式引用。 */
export function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}
