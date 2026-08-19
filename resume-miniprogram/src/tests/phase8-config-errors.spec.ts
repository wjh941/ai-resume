import { describe, expect, it } from "vitest"

import { toUserMessage } from "../services/http"


describe("production configuration error guidance", () => {
  it("explains missing SMS setup without exposing server detail", () => {
    expect(toUserMessage(new Error("SMS delivery is not configured or temporarily unavailable.")))
      .toBe("SMS sign-in is not configured for this environment. Contact the service administrator.")
  })

  it("explains the WeChat HTTPS callback requirement", () => {
    expect(toUserMessage(new Error("WeChat OAuth callback deployment requires an HTTPS whitelisted redirect domain.")))
      .toBe("WeChat sign-in needs an approved HTTPS callback domain.")
  })

  it("explains unavailable payment configuration", () => {
    expect(toUserMessage(new Error("Payment channel is not configured.")))
      .toBe("Payment is not configured for this environment. Choose another available option.")
  })
})
