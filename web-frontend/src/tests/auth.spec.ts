import { describe, expect, it, vi } from "vitest"

import { SLOW_REQUEST_TIMEOUT_MS } from "../lib/api"
import { loginWithPassword, loginWithPhone, registerAccount } from "../lib/auth"

// 登录是会话第一步，恰好最容易撞上后端冷启动——三条链路都必须携带慢超时。
const slowOptions = { timeoutMs: SLOW_REQUEST_TIMEOUT_MS }

describe("loginWithPassword", () => {
  it("uses the existing password-login endpoint and stores its JWT result", async () => {
    const request = vi.fn().mockResolvedValue({
      token: "jwt-token",
      user: { user_id: "u-1", role: "user", account: "career-user" },
    })

    await expect(loginWithPassword(request, "career-user", "secure-password")).resolves.toEqual({
      token: "jwt-token",
      user: { user_id: "u-1", role: "user", account: "career-user" },
    })

    expect(request).toHaveBeenCalledWith("/api/auth/login-password", {
      method: "POST",
      body: JSON.stringify({ account: "career-user", password: "secure-password" }),
    }, slowOptions)
  })
})

it("uses the existing phone-login endpoint", async () => {
  const request = vi.fn().mockResolvedValue({ token: "jwt-token", user: { user_id: "u-1", role: "user" } })

  await loginWithPhone(request, "13800138000", "123456")

  expect(request).toHaveBeenCalledWith("/api/auth/login-phone", {
    method: "POST",
    body: JSON.stringify({ phone: "13800138000", code: "123456" }),
  }, slowOptions)
})

it("uses the existing password registration endpoint", async () => {
  const request = vi.fn().mockResolvedValue({ token: "jwt-token", user: { user_id: "u-1", role: "user" } })

  await registerAccount(request, "career-user", "secure-password")

  expect(request).toHaveBeenCalledWith("/api/auth/register-password", {
    method: "POST",
    body: JSON.stringify({ account: "career-user", password: "secure-password" }),
  }, slowOptions)
})
