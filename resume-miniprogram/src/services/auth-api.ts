import { request, SLOW_REQUEST_TIMEOUT_MS } from "./http"
import type { AuthUser, PhoneCodeResult } from "../types/auth"

type BackendAuthUser = { user_id: string; phone: string; role?: string; account?: string }

function mapUser(user: BackendAuthUser): AuthUser {
  return {
    userId: user.user_id,
    phone: user.phone,
    role: user.role === "operator" ? "operator" : "user",
    account: typeof user.account === "string" ? user.account : undefined,
  }
}

// 登录链路是每次会话的第一步，最容易撞上免费托管实例的冷启动（30-50 秒），
// 统一放宽到慢超时，避免服务唤醒前把用户挡在门外。
function authOptions() {
  return { timeoutMs: SLOW_REQUEST_TIMEOUT_MS }
}

export async function sendPhoneCode(phone: string): Promise<PhoneCodeResult> {
  const data = await request<{ phone: string; demo_code?: string; message: string }>(
    "/api/auth/send-code",
    "POST",
    { phone },
    authOptions(),
  )
  return { phone: data.phone, demoCode: data.demo_code, message: data.message }
}

export async function loginPhone(phone: string, code: string): Promise<{ token: string; user: AuthUser }> {
  const data = await request<{ token: string; user: BackendAuthUser }>(
    "/api/auth/login-phone",
    "POST",
    { phone, code },
    authOptions(),
  )
  return { token: data.token, user: mapUser(data.user) }
}

export async function registerPasswordAccount(account: string, password: string): Promise<{ token: string; user: AuthUser }> {
  const data = await request<{ token: string; user: BackendAuthUser }>(
    "/api/auth/register-password",
    "POST",
    { account, password },
    authOptions(),
  )
  return { token: data.token, user: mapUser(data.user) }
}

export async function loginPasswordAccount(account: string, password: string): Promise<{ token: string; user: AuthUser }> {
  const data = await request<{ token: string; user: BackendAuthUser }>(
    "/api/auth/login-password",
    "POST",
    { account, password },
    authOptions(),
  )
  return { token: data.token, user: mapUser(data.user) }
}

export async function getCurrentUser(): Promise<AuthUser> {
  return mapUser(await request<BackendAuthUser>("/api/auth/me"))
}

export async function logout(): Promise<void> {
  await request<{ logged_out: boolean }>("/api/auth/logout", "POST")
}
