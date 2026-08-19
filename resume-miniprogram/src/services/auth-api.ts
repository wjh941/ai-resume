import { request } from "./http"
import type { AuthUser, PhoneCodeResult } from "../types/auth"

type BackendAuthUser = { user_id: string; phone: string }

function mapUser(user: BackendAuthUser): AuthUser {
  return { userId: user.user_id, phone: user.phone }
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

export async function getCurrentUser(): Promise<AuthUser> {
  return mapUser(await request<BackendAuthUser>("/api/auth/me"))
}

export async function logout(): Promise<void> {
  await request<{ logged_out: boolean }>("/api/auth/logout", "POST")
}
