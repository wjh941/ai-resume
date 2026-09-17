import { afterEach, describe, expect, it, vi } from "vitest"

const originalEnv = { ...import.meta.env }

async function loadApiWithEnv(env: Record<string, string>) {
  vi.resetModules()
  ;(import.meta.env as Record<string, unknown>).VITE_API_BASE_URL = env.VITE_API_BASE_URL ?? ""
  return await import("../lib/api")
}

afterEach(() => {
  Object.assign(import.meta.env, originalEnv)
  vi.unstubAllGlobals()
})

describe("API base url", () => {
  it("keeps relative paths when VITE_API_BASE_URL is empty (dev proxy)", async () => {
    const { requestApi } = await loadApiWithEnv({ VITE_API_BASE_URL: "" })
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ code: "ok", data: { ok: true } }), { status: 200 }))
    vi.stubGlobal("fetch", fetchMock)
    await requestApi("/api/auth/session")
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/session", expect.anything())
  })

  it("prefixes the configured backend origin, trimming trailing slashes", async () => {
    const { requestApi } = await loadApiWithEnv({ VITE_API_BASE_URL: "https://backend.example.com/" })
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ code: "ok", data: { ok: true } }), { status: 200 }))
    vi.stubGlobal("fetch", fetchMock)
    await requestApi("/api/auth/session")
    expect(fetchMock).toHaveBeenCalledWith("https://backend.example.com/api/auth/session", expect.anything())
  })
})
