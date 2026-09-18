import { SLOW_REQUEST_TIMEOUT_MS } from "./api"
import type { Session, SessionUser } from "./session"
import { saveSession } from "./session"

export type ApiRequester = <T>(
  path: string,
  init?: RequestInit,
  options?: { timeoutMs?: number },
) => Promise<T>

type AuthResponse = {
  token: string
  user: SessionUser
}

async function authenticate(
  request: ApiRequester,
  path: string,
  payload: Record<string, string>,
): Promise<Session> {
  const response = await request<AuthResponse>(
    path,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    // 登录是每次会话的第一步，恰好最容易撞上免费托管实例的冷启动
    // （30-50 秒），默认 15 秒超时会在服务唤醒前把用户挡在门外。
    { timeoutMs: SLOW_REQUEST_TIMEOUT_MS },
  )
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
