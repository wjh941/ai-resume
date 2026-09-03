import { afterEach, describe, expect, it, vi } from "vitest"

import { downloadApi, requestApi } from "../lib/api"
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

    await expect(requestApi("/api/auth/me")).rejects.toMatchObject({
      message: "expired",
      status: 401,
    })

    expect(localStorage.getItem("resume-web-session")).toBeNull()
  })

  it("notifies the app when an API session expires", async () => {
    const dispatchEvent = vi.fn()
    vi.stubGlobal("window", { dispatchEvent })
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "expired" }), { status: 401 })),
    )

    await expect(requestApi("/api/overview")).rejects.toMatchObject({ status: 401 })

    expect(dispatchEvent).toHaveBeenCalledWith(expect.objectContaining({ type: "resume-web-session-expired" }))
  })

  it("normalizes network failures into an API request error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")))

    await expect(requestApi("/api/overview")).rejects.toMatchObject({
      name: "ApiRequestError",
      status: 0,
    })
  })

  it("normalizes non-JSON responses instead of leaking a parser error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response("upstream unavailable", { status: 502 }),
    ))

    await expect(requestApi("/api/overview")).rejects.toMatchObject({
      name: "ApiRequestError",
      status: 502,
    })
  })

  it("preserves an intentional abort for callers that need cancellation semantics", async () => {
    const abortError = new DOMException("The operation was aborted", "AbortError")
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(abortError))

    await expect(requestApi("/api/overview")).rejects.toBe(abortError)
  })

  it("accepts an empty 204 response for side-effect requests", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 204 })))

    await expect(requestApi<void>("/api/draft/d-1", { method: "DELETE" })).resolves.toBeUndefined()
  })

  it("downloads authenticated binary data", async () => {
    installStorage()
    saveSession("jwt-token", { user_id: "u-1", role: "user" })
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("zip-bytes", { status: 200, headers: { "Content-Type": "application/zip" } }),
    )
    vi.stubGlobal("fetch", fetchMock)

    const blob = await downloadApi("/api/account/data-export")

    expect(blob).toBeInstanceOf(Blob)
    expect(await blob.text()).toBe("zip-bytes")
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer jwt-token")
  })
})
