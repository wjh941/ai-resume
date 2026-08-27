import { readFileSync } from "node:fs"
import { describe, expect, it } from "vitest"

import { prependOrder, replaceOrder } from "../lib/membership-workflow"
import type { MembershipOrder } from "../lib/membership"

const order = (id: string, paymentStatus = "pending"): MembershipOrder => ({ orderId: id, packageType: "monthly", totalAmount: 29, paymentStatus, paymentChannel: paymentStatus === "paid" ? "demo" : null, createTime: "t1", entitlementExpireTime: paymentStatus === "paid" ? "t2" : null })
const membershipView = () => readFileSync(new URL("../views/MembershipView.vue", import.meta.url), "utf8")

describe("membership workflow helpers", () => {
  it("keeps a created order pending until the payment response replaces it", () => {
    const pending = prependOrder([], order("o-1"))
    expect(pending[0].paymentStatus).toBe("pending")
    expect(replaceOrder(pending, order("o-1", "paid"))[0].paymentStatus).toBe("paid")
  })

  it("does not alter unrelated orders after payment", () => {
    expect(replaceOrder([order("o-1"), order("o-2")], order("o-1", "paid")).find((item) => item.orderId === "o-2")?.paymentStatus).toBe("pending")
  })

  it("disables pending payment and explains when the payment capability is unavailable", () => {
    const source = membershipView()

    expect(source).toContain("CAPABILITIES_KEY")
    expect(source).toContain("paymentEnabled")
    expect(source).toContain("paymentNotice")
    expect(source).toContain(':disabled="!paymentEnabled')
    expect(source).toContain("{{ paymentNotice }}")
    expect(source).toContain("if (!paymentEnabled.value) {")
    expect(source).toContain("capabilityNotice.value = paymentNotice.value")
    expect(source).toContain("if (paymentMode.value !== \"demo\") return")
  })

  it("does not render a disabled payment notice as a success message", () => {
    const source = membershipView()

    expect(source).toContain('const capabilityNotice = ref("")')
    expect(source).toContain('v-if="capabilityNotice" class="source-notice"')
    expect(source).not.toContain('v-if="capabilityNotice" class="notice-success"')
  })

  it("labels demo payment and only calls the demo callback in demo mode", () => {
    const source = membershipView()

    expect(source).toContain("paymentMode")
    expect(source).toContain("演示支付")
    expect(source).toMatch(/paymentMode\.value !== "demo"[\s\S]+completeDemoPayment/)
  })

  it("keeps membership packages and order history rendered independently of payment state", () => {
    const source = membershipView()

    expect(source).toContain('<section class="membership-packages decision-surface">')
    expect(source).toContain('<section class="order-panel">')
    expect(source).not.toMatch(/v-if="!paymentEnabled[^"]*"[^>]*class="membership-packages/)
    expect(source).not.toMatch(/v-if="!paymentEnabled[^"]*"[^>]*class="order-panel/)
  })
})
