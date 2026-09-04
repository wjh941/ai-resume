import { describe, expect, it } from "vitest"

import { ApiRequestError, ApiTimeoutError } from "../lib/api"
import { getApiErrorMessage } from "../lib/api-error"

describe("getApiErrorMessage", () => {
  it("explains request timeouts", () => {
    expect(getApiErrorMessage(new ApiTimeoutError(), "fallback")).toBe("请求超时，请稍后重试")
  })

  it("explains expired sessions and forbidden capabilities", () => {
    expect(getApiErrorMessage(new ApiRequestError("expired", 401), "fallback")).toBe("登录已过期，请重新登录后继续")
    expect(getApiErrorMessage(new ApiRequestError("forbidden", 403), "fallback")).toBe("当前功能暂不可用，请查看会员权益")
  })

  it("explains network failures", () => {
    expect(getApiErrorMessage(new TypeError("Failed to fetch"), "fallback")).toBe("网络连接失败，请检查网络后重试")
  })

  it("keeps the caller fallback for unknown failures", () => {
    expect(getApiErrorMessage(new Error("unexpected"), "请稍后重试")).toBe("请稍后重试")
  })
})
