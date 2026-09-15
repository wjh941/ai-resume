import { afterEach, describe, expect, it } from "vitest"

import { ApiRequestError, buildQuery, request, resolveApiUrl, toUserMessage } from "../services/http"

type RequestCall = Record<string, unknown>
const calls: RequestCall[] = []
let responder: (options: RequestCall) => Promise<{ statusCode?: number; data: unknown }> | never =
  async () => ({ statusCode: 200, data: { code: "ok", data: {} } })

function installUni(): void {
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async (options: RequestCall) => {
      calls.push(options)
      return responder(options)
    },
  }
}

afterEach(() => {
  delete (globalThis as typeof globalThis & { uni?: unknown }).uni
  calls.length = 0
})

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

describe("toUserMessage", () => {
  it("hides raw server details from end users", () => {
    expect(toUserMessage(new Error("Traceback (most recent call last): secret"))).toBe(
      "服务暂时不可用，请稍后重试。",
    )
  })
})

describe("buildQuery", () => {
  it("skips empty values and encodes keys and values", () => {
    expect(buildQuery({ q: "数据 分析", page: 2, empty: "", missing: undefined, nil: null, ok: true })).toBe(
      "?q=%E6%95%B0%E6%8D%AE%20%E5%88%86%E6%9E%90&page=2&ok=true",
    )
  })

  it("returns an empty string when every value is blank", () => {
    expect(buildQuery({ a: undefined, b: null, c: "" })).toBe("")
  })
})

describe("request", () => {
  it("appends the normalized query string to the request URL", async () => {
    installUni()
    process.env.UNI_PLATFORM = "h5"
    await request("/api/role/suggestions", "GET", undefined, { query: { q: "前端 工程", limit: 5 } })
    expect(calls[0].url).toBe("/api/role/suggestions?q=%E5%89%8D%E7%AB%AF%20%E5%B7%A5%E7%A8%8B&limit=5")
    delete process.env.UNI_PLATFORM
  })

  it("sends the auth header and a bounded timeout", async () => {
    installUni()
    process.env.UNI_PLATFORM = "h5"
    await request("/api/ping", "GET")
    expect(calls[0].timeout).toBe(15000)
    expect(calls[0].header).toEqual({})
    delete process.env.UNI_PLATFORM
  })

  it("classifies transport failures as retryable network errors", async () => {
    installUni()
    responder = async () => { throw new Error("request:fail") }
    await expect(request("/api/ping", "POST")).rejects.toMatchObject({ kind: "network" })
  })

  it("retries an idempotent GET once after a transient failure", async () => {
    installUni()
    let attempts = 0
    responder = async () => {
      attempts += 1
      if (attempts === 1) throw new Error("request:fail timeout")
      return { statusCode: 200, data: { code: "ok", data: { value: 1 } } }
    }
    await expect(request("/api/ping", "GET")).resolves.toEqual({ value: 1 })
    expect(attempts).toBe(2)
  })

  it("does not retry non-idempotent POST requests", async () => {
    installUni()
    let attempts = 0
    responder = async () => {
      attempts += 1
      throw new Error("request:fail")
    }
    await expect(request("/api/draft/save", "POST", {})).rejects.toMatchObject({ kind: "network" })
    expect(attempts).toBe(1)
  })

  it("retries a GET once even for 5xx, then surfaces the server error", async () => {
    installUni()
    responder = async () => ({ statusCode: 500, data: { code: "database_error", message: "数据库操作失败", data: {} } })
    await expect(request("/api/ping", "GET")).rejects.toMatchObject({ kind: "http", statusCode: 500 })
    expect(calls).toHaveLength(2)
  })

  it("classifies backend validation failures as business errors", async () => {
    installUni()
    responder = async () => ({ statusCode: 422, data: { code: "validation_error", message: "请求校验失败", data: {} } })
    const error = await request("/api/ping", "POST").catch((reason: unknown) => reason)
    expect(error).toBeInstanceOf(ApiRequestError)
    expect((error as ApiRequestError).kind).toBe("business")
    expect((error as ApiRequestError).code).toBe("validation_error")
    expect((error as ApiRequestError).message).toBe("请求校验失败")
  })

  it("treats non-JSON gateway responses as server errors instead of crashing", async () => {
    installUni()
    responder = async () => ({ statusCode: 200, data: "<html>Bad Gateway</html>" })
    await expect(request("/api/ping", "GET")).rejects.toMatchObject({ kind: "http" })
  })

  it("treats a 2xx non-envelope payload as a server-side contract error", async () => {
    installUni()
    responder = async () => ({ statusCode: 200, data: [1, 2, 3] })
    await expect(request("/api/ping", "GET")).rejects.toMatchObject({ kind: "http" })
  })

  it("surfaces business failure messages from a 200 envelope", async () => {
    installUni()
    responder = async () => ({ statusCode: 200, data: { code: "ai_not_configured", message: "AI 服务未配置", data: {} } })
    await expect(request("/api/ping", "POST")).rejects.toMatchObject({
      kind: "business",
      code: "ai_not_configured",
      message: "AI 服务未配置",
    })
  })
})
