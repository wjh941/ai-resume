import type { Session, SessionUser } from "./session"
import { saveSession } from "./session"

export type ApiRequester = <T>(path: string, init?: RequestInit) => Promise<T>

type AuthResponse = {
  token: string
  user: SessionUser
}

async function authenticate(
  request: ApiRequester,
  path: string,
  payload: Record<string, string>,
): Promise<Session> {
  const response = await request<AuthResponse>(path, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const session = { token: response.token, user: response.user }
  saveSession(session.token, session.user)
  return session
}

export function loginWithPassword(
  request: ApiRequester,
  account: string,
  password: string,
): Promise<Session> {
  return authenticate(request, "/api/auth/login-password", { account, password })
}

export function loginWithPhone(
  request: ApiRequester,
  phone: string,
  code: string,
): Promise<Session> {
  return authenticate(request, "/api/auth/login-phone", { phone, code })
}

export function registerAccount(
  request: ApiRequester,
  account: string,
  password: string,
): Promise<Session> {
  return authenticate(request, "/api/auth/register-password", { account, password })
}
