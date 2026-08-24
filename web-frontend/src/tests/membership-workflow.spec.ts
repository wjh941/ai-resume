import { describe, expect, it } from "vitest"

import { prependOrder, replaceOrder } from "../lib/membership-workflow"
import type { MembershipOrder } from "../lib/membership"

const order = (id: string, paymentStatus = "pending"): MembershipOrder => ({ orderId: id, packageType: "monthly", totalAmount: 29, paymentStatus, paymentChannel: paymentStatus === "paid" ? "demo" : null, createTime: "t1", entitlementExpireTime: paymentStatus === "paid" ? "t2" : null })

describe("membership workflow helpers", () => {
  it("keeps a created order pending until the payment response replaces it", () => {
    const pending = prependOrder([], order("o-1"))
    expect(pending[0].paymentStatus).toBe("pending")
    expect(replaceOrder(pending, order("o-1", "paid"))[0].paymentStatus).toBe("paid")
  })

  it("does not alter unrelated orders after payment", () => {
    expect(replaceOrder([order("o-1"), order("o-2")], order("o-1", "paid")).find((item) => item.orderId === "o-2")?.paymentStatus).toBe("pending")
  })
})
