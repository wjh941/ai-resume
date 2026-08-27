import { afterEach, describe, expect, it, vi } from "vitest"

import { requestApi } from "../lib/api"
import {
  defaultCapabilities,
  getCapabilities,
  isCapabilityEnabled,
  mapCapabilities,
} from "../lib/capabilities"

vi.mock("../lib/api", () => ({
  requestApi: vi.fn(),
}))

const requestApiMock = vi.mocked(requestApi)

describe("capabilities", () => {
  afterEach(() => {
    requestApiMock.mockReset()
  })

  it("maps every supported backend feature without passing unknown fields through", () => {
    const capabilities = mapCapabilities({
      features: {
        resume_import: { enabled: true, mode: "real", notice: "已启用", extra: "ignore" },
        sms_login: { enabled: true, mode: "demo", notice: "演示模式" },
        wechat_oauth: { enabled: false, mode: "disabled", notice: "未配置" },
        payment: { enabled: true, mode: "real", notice: "已启用" },
        push_notifications: { enabled: false, mode: "demo", notice: "暂不可用" },
        job_matching: { enabled: true, mode: "real", notice: "已启用" },
        unknown_feature: { enabled: true, mode: "real", notice: "不要透传" },
      },
    })

    expect(capabilities).toEqual({
      resumeImport: { enabled: true, mode: "real", notice: "已启用" },
      smsLogin: { enabled: true, mode: "demo", notice: "演示模式" },
      wechatOauth: { enabled: false, mode: "disabled", notice: "未配置" },
      payment: { enabled: true, mode: "real", notice: "已启用" },
      pushNotifications: { enabled: false, mode: "demo", notice: "暂不可用" },
      jobMatching: { enabled: true, mode: "real", notice: "已启用" },
    })
  })

  it("disables features with missing or invalid fields", () => {
    const capabilities = mapCapabilities({
      features: {
        resume_import: { enabled: true, mode: "real" },
        sms_login: { enabled: "true", mode: "real", notice: "错误类型" },
        wechat_oauth: { enabled: true, mode: "unknown", notice: "错误模式" },
        payment: { enabled: true, mode: "real", notice: "   " },
      },
    })

    expect(capabilities.resumeImport.enabled).toBe(false)
    expect(capabilities.smsLogin.enabled).toBe(false)
    expect(capabilities.wechatOauth.enabled).toBe(false)
    expect(capabilities.payment.enabled).toBe(false)
    for (const name of ["resumeImport", "smsLogin", "wechatOauth", "payment"] as const) {
      expect(capabilities[name].mode).toBe("disabled")
      expect(capabilities[name].notice.trim()).not.toBe("")
    }
  })

  it("uses defaults for null, arrays, and malformed features payloads", () => {
    expect(mapCapabilities(null)).toEqual(defaultCapabilities())
    expect(mapCapabilities([])).toEqual(defaultCapabilities())
    expect(mapCapabilities({ features: null })).toEqual(defaultCapabilities())
    expect(mapCapabilities({ features: [] })).toEqual(defaultCapabilities())
  })

  it("fetches capabilities from health and falls back when the request fails", async () => {
    requestApiMock.mockResolvedValueOnce({
      features: { payment: { enabled: true, mode: "real", notice: "可支付" } },
    })
    await expect(getCapabilities()).resolves.toMatchObject({
      payment: { enabled: true, mode: "real", notice: "可支付" },
    })
    expect(requestApiMock).toHaveBeenCalledWith("/health")

    requestApiMock.mockRejectedValueOnce(new Error("offline"))
    await expect(getCapabilities()).resolves.toEqual(defaultCapabilities())
  })

  it("only enables non-disabled capabilities", () => {
    const capabilities = defaultCapabilities()
    capabilities.resumeImport = { enabled: true, mode: "real", notice: "可用" }
    capabilities.smsLogin = { enabled: true, mode: "disabled", notice: "关闭" }
    capabilities.payment = { enabled: false, mode: "demo", notice: "关闭" }

    expect(isCapabilityEnabled(capabilities, "resumeImport")).toBe(true)
    expect(isCapabilityEnabled(capabilities, "smsLogin")).toBe(false)
    expect(isCapabilityEnabled(capabilities, "payment")).toBe(false)
  })
})
