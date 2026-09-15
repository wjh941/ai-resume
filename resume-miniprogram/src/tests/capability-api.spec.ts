import { beforeEach, describe, expect, it } from "vitest"

import { getCapabilities, isCapabilityEnabled, mapCapabilities } from "../services/capability-api"

beforeEach(() => {
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async () => ({
      statusCode: 200,
      data: {
        code: "ok",
        data: {
          features: {
            resume_import: { enabled: true, mode: "real", notice: "支持简历导入。" },
            sms_login: { enabled: false, mode: "disabled", notice: "短信登录暂不可用。" },
            wechat_oauth: { enabled: true, mode: "real", notice: "支持微信登录。" },
            payment: { enabled: true, mode: "demo", notice: "当前使用演示支付。" },
            push_notifications: { enabled: false, mode: "disabled", notice: "推送暂不可用。" },
            job_matching: { enabled: true, mode: "demo", notice: "使用本地岗位匹配。" },
          },
        },
      },
    }),
  }
})

describe("capability API", () => {
  it("maps public health feature flags to camel-case keys", async () => {
    const capabilities = await getCapabilities()

    expect(capabilities.resumeImport).toMatchObject({ enabled: true, mode: "real" })
    expect(capabilities.smsLogin.enabled).toBe(false)
    expect(capabilities.wechatOauth.mode).toBe("real")
    expect(capabilities.jobMatching.mode).toBe("demo")
    expect(isCapabilityEnabled(capabilities, "payment")).toBe(true)
  })

  it("defaults optional capabilities to disabled when health fails", async () => {
    ;(globalThis as typeof globalThis & { uni: { request: () => Promise<unknown> } }).uni.request = async () => {
      throw new Error("network down")
    }

    const capabilities = await getCapabilities()

    expect(Object.values(capabilities).every((feature) => feature.enabled === false)).toBe(true)
    expect(capabilities.resumeImport.notice).toBeTruthy()
    expect(isCapabilityEnabled(capabilities, "payment")).toBe(false)
  })

  it("rejects malformed feature records instead of coercing them", async () => {
    const capabilities = mapCapabilities({
      features: {
        payment: { enabled: "yes" as unknown as boolean, mode: "real", notice: "ok" },
        sms_login: { enabled: true, mode: "unknown" as string, notice: "ok" },
      },
    })

    expect(capabilities.payment.enabled).toBe(false)
    expect(capabilities.payment.mode).toBe("disabled")
    expect(capabilities.smsLogin.enabled).toBe(false)
  })

  it("falls back safely for malformed health payloads", () => {
    const nullPayload = mapCapabilities(null)
    const invalidFeatures = mapCapabilities({ features: "invalid" })

    expect(nullPayload.payment.mode).toBe("disabled")
    expect(invalidFeatures.jobMatching.enabled).toBe(false)
  })
})
