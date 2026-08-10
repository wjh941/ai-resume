import { describe, expect, it } from "vitest"

import { resolveApiUrl } from "../services/http"

describe("resolveApiUrl", () => {
  it("uses the configured public API URL and normalizes its trailing slash", () => {
    expect(resolveApiUrl("https://api.example.com/", "mp-weixin", "/api/job/query")).toBe(
      "https://api.example.com/api/job/query",
    )
  })

  it("uses a relative URL for H5 when a public API URL is not configured", () => {
    expect(resolveApiUrl("", "h5", "/api/job/query")).toBe("/api/job/query")
  })

  it("uses a relative URL when the platform is not injected by the test runtime", () => {
    expect(resolveApiUrl("", undefined, "/api/job/query")).toBe("/api/job/query")
  })

  it("requires an explicit public API URL for a mini-program build", () => {
    expect(() => resolveApiUrl("", "mp-weixin", "/api/job/query")).toThrow(
      "VITE_RESUME_API_URL",
    )
  })
})
