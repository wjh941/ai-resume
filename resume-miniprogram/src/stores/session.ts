const CLIENT_ID_KEY = "resume_demo_client_id"
const AUTH_TOKEN_KEY = "resume_demo_auth_token"
const AUTH_USER_KEY = "resume_demo_auth_user"

export type AuthSessionUser = {
  userId: string
  phone: string
  role: "user" | "operator"
  account?: string
}

type UniStorage = {
  getStorageSync(key: string): unknown
  setStorageSync(key: string, value: unknown): void
  removeStorageSync?(key: string): void
}

function storage(): UniStorage | null {
  const candidate = (globalThis as typeof globalThis & { uni?: UniStorage }).uni
  return candidate
    && typeof candidate.getStorageSync === "function"
    && typeof candidate.setStorageSync === "function"
    ? candidate
    : null
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

export function getAuthToken(): string | null {
  const token = storage()?.getStorageSync(AUTH_TOKEN_KEY)
  return typeof token === "string" && token ? token : null
}

export function getAuthUser(): AuthSessionUser | null {
  const user = storage()?.getStorageSync(AUTH_USER_KEY)
  if (!user || typeof user !== "object") return null
  const candidate = user as Partial<AuthSessionUser>
  return typeof candidate.userId === "string" && typeof candidate.phone === "string"
    ? {
        userId: candidate.userId,
        phone: candidate.phone,
        role: candidate.role === "operator" ? "operator" : "user",
        account: typeof candidate.account === "string" ? candidate.account : undefined,
      }
    : null
}

export function setAuthSession(
  token: string,
  user: Omit<AuthSessionUser, "role"> & Partial<Pick<AuthSessionUser, "role">>,
): void {
  const uniStorage = storage()
  uniStorage?.setStorageSync(AUTH_TOKEN_KEY, token)
  uniStorage?.setStorageSync(AUTH_USER_KEY, { ...user, role: user.role === "operator" ? "operator" : "user" })
}

export function clearAuthSession(): void {
  const uniStorage = storage()
  if (uniStorage?.removeStorageSync) {
    uniStorage.removeStorageSync(AUTH_TOKEN_KEY)
    uniStorage.removeStorageSync(AUTH_USER_KEY)
    return
  }
  uniStorage?.setStorageSync(AUTH_TOKEN_KEY, "")
  uniStorage?.setStorageSync(AUTH_USER_KEY, "")
}
