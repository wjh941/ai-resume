import { beforeEach, describe, expect, it } from "vitest"

import { loginPasswordAccount, registerPasswordAccount } from "../services/auth-api"
import { getAuthUser, setAuthSession } from "../stores/session"

const storage = new Map<string, unknown>()
const requests: Array<Record<string, unknown>> = []

beforeEach(() => {
  storage.clear()
  requests.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
    removeStorageSync: (key: string) => storage.delete(key),
    request: async (options: Record<string, unknown>) => {
      requests.push(options)
      return {
        statusCode: 200,
        data: {
          code: "ok",
          message: "",
          data: {
            token: "password-token",
            user: { user_id: "user-password", phone: "local:user-password", role: "user", account: "owner" },
          },
        },
      }
    },
  }
})

describe("password account authentication", () => {
  it("sends registration credentials and maps the account identity", async () => {
    const session = await registerPasswordAccount("Owner", "a-strong-password")

    expect(requests[0]).toMatchObject({
      url: "/api/auth/register-password",
      method: "POST",
      data: { account: "Owner", password: "a-strong-password" },
    })
    expect(session.user).toMatchObject({ userId: "user-password", account: "owner", role: "user" })
  })

  it("sends password login credentials and preserves the account session metadata", async () => {
    const session = await loginPasswordAccount("owner", "a-strong-password")
    setAuthSession(session.token, session.user)

    expect(requests[0]).toMatchObject({
      url: "/api/auth/login-password",
      method: "POST",
      data: { account: "owner", password: "a-strong-password" },
    })
    expect(getAuthUser()).toMatchObject({ userId: "user-password", account: "owner" })
  })
})
