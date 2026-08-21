import { afterEach, describe, expect, it, vi } from "vitest"

import { requestApi } from "../lib/api"
import { clearSession, saveSession } from "../lib/session"

function installStorage() {
  const values = new Map<string, string>()
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
    },
  })
}

describe("requestApi", () => {
  afterEach(() => {
    clearSession()
    vi.unstubAllGlobals()
  })

  it("adds the saved JWT bearer token to an authenticated request", async () => {
    installStorage()
    saveSession("jwt-token", { user_id: "u-1", role: "user" })
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ code: "ok", data: { id: 1 } }), { status: 200 }),
    )
    vi.stubGlobal("fetch", fetchMock)

    await requestApi("/api/auth/me")

    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer jwt-token")
  })

  it("clears the saved session after a 401 response", async () => {
    installStorage()
    saveSession("expired-token", { user_id: "u-1", role: "user" })
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "expired" }), { status: 401 })),
    )

    await expect(requestApi("/api/auth/me")).rejects.toThrow("expired")

    expect(localStorage.getItem("resume-web-session")).toBeNull()
  })
})
