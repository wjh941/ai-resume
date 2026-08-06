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
  const bytes = new Uint8Array(16)
  if (typeof crypto !== "undefined" && crypto.getRandomValues) {
    crypto.getRandomValues(bytes)
  } else {
    for (let index = 0; index < bytes.length; index += 1) bytes[index] = Math.floor(Math.random() * 256)
  }
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("")
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
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
