export type SessionUser = {
  user_id: string
  role: string
  phone?: string
  account?: string
}

export type Session = {
  token: string
  user: SessionUser
}

const sessionKey = "resume-web-session"

function getStorage(): Storage | null {
  return typeof localStorage === "undefined" ? null : localStorage
}

export function saveSession(token: string, user: SessionUser): void {
  getStorage()?.setItem(sessionKey, JSON.stringify({ token, user } satisfies Session))
}

export function readSession(): Session | null {
  const stored = getStorage()?.getItem(sessionKey)
  if (!stored) return null

  try {
    const session = JSON.parse(stored) as Session
    return session.token && session.user?.user_id ? session : null
  } catch {
    clearSession()
    return null
  }
}

export function clearSession(): void {
  getStorage()?.removeItem(sessionKey)
}
