import { describe, expect, it } from "vitest"

import { toUserMessage } from "../services/http"


describe("production configuration error guidance", () => {
  it("explains missing SMS setup without exposing server detail", () => {
    expect(toUserMessage(new Error("SMS delivery is not configured or temporarily unavailable.")))
      .toBe("当前环境未配置 SMS 登录，请联系服务管理员。")
  })

  it("explains the WeChat HTTPS callback requirement", () => {
    expect(toUserMessage(new Error("WeChat OAuth callback deployment requires an HTTPS whitelisted redirect domain.")))
      .toBe("微信登录需要已配置的 HTTPS 回调域名。")
  })

  it("explains unavailable payment configuration", () => {
    expect(toUserMessage(new Error("Payment channel is not configured.")))
      .toBe("当前未配置支付服务，请选择其他可用方式。")
  })
})
