import { describe, expect, it, vi } from "vitest"

import { loginWithPassword, loginWithPhone, registerAccount } from "../lib/auth"

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
    })
  })
})

it("uses the existing phone-login endpoint", async () => {
  const request = vi.fn().mockResolvedValue({ token: "jwt-token", user: { user_id: "u-1", role: "user" } })

  await loginWithPhone(request, "13800138000", "123456")

  expect(request).toHaveBeenCalledWith("/api/auth/login-phone", {
    method: "POST",
    body: JSON.stringify({ phone: "13800138000", code: "123456" }),
  })
})

it("uses the existing password registration endpoint", async () => {
  const request = vi.fn().mockResolvedValue({ token: "jwt-token", user: { user_id: "u-1", role: "user" } })

  await registerAccount(request, "career-user", "secure-password")

  expect(request).toHaveBeenCalledWith("/api/auth/register-password", {
    method: "POST",
    body: JSON.stringify({ account: "career-user", password: "secure-password" }),
  })
})
