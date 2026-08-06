const CLIENT_ID_KEY = "resume_demo_client_id"

type UniStorage = {
  getStorageSync(key: string): unknown
  setStorageSync(key: string, value: unknown): void
}

function storage(): UniStorage | null {
  const candidate = (globalThis as typeof globalThis & { uni?: UniStorage }).uni
  return candidate ?? null
}

function generateId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID()
  }
  return `demo-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function getClientId(): string {
  const uniStorage = storage()
  if (!uniStorage) {
    return CLIENT_ID_KEY
  }
  const existing = uniStorage.getStorageSync(CLIENT_ID_KEY)
  if (typeof existing === "string" && existing) {
    return existing
  }
  const clientId = generateId()
  uniStorage.setStorageSync(CLIENT_ID_KEY, clientId)
  return clientId
}
