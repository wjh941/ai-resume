import { request } from "./http"
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

export async function sendPhoneCode(phone: string): Promise<PhoneCodeResult> {
  const data = await request<{ phone: string; demo_code?: string; message: string }>(
    "/api/auth/send-code",
    "POST",
    { phone },
  )
  return { phone: data.phone, demoCode: data.demo_code, message: data.message }
}

export async function loginPhone(phone: string, code: string): Promise<{ token: string; user: AuthUser }> {
  const data = await request<{ token: string; user: BackendAuthUser }>(
    "/api/auth/login-phone",
    "POST",
    { phone, code },
  )
  return { token: data.token, user: mapUser(data.user) }
}

export async function registerPasswordAccount(account: string, password: string): Promise<{ token: string; user: AuthUser }> {
  const data = await request<{ token: string; user: BackendAuthUser }>(
    "/api/auth/register-password",
    "POST",
    { account, password },
  )
  return { token: data.token, user: mapUser(data.user) }
}

export async function loginPasswordAccount(account: string, password: string): Promise<{ token: string; user: AuthUser }> {
  const data = await request<{ token: string; user: BackendAuthUser }>(
    "/api/auth/login-password",
    "POST",
    { account, password },
  )
  return { token: data.token, user: mapUser(data.user) }
}

export async function getCurrentUser(): Promise<AuthUser> {
  return mapUser(await request<BackendAuthUser>("/api/auth/me"))
}

export async function logout(): Promise<void> {
  await request<{ logged_out: boolean }>("/api/auth/logout", "POST")
}
