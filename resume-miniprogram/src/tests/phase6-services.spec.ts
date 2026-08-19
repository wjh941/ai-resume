import { beforeEach, describe, expect, it } from "vitest"

import { requestAccountDeletion, requestAccountScope } from "../services/account-api"
import { listFavoriteJobs, setJobMatchSubscription } from "../services/job-collection-api"
import { completeDemoPayment, listMembershipPackages, listOrders } from "../services/membership-api"

const calls: Array<{ url: string; method?: string; data?: unknown }> = []

beforeEach(() => {
  calls.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async (options: { url: string; method?: string; data?: unknown }) => {
      calls.push(options)
      const dataByPath: Record<string, unknown> = {
        "/api/account/data-scope": { categories: ["resume_drafts"], retention_note: "Acknowledgement only" },
        "/api/account/deletion-request": { status: "requested", message: "No account data has been deleted." },
        "/api/job-collection/favorites": { items: [{ id: "fav-1", role_name: "Data Engineer", note: "Review", created_at: "2026-08-19T00:00:00+00:00" }] },
        "/api/job-collection/subscription": { enabled: true },
        "/api/pay/package-list": { items: [{ package_type: "monthly", name: "Monthly", vip_level: "basic", duration_days: 30, total_amount: 2900, benefits: ["Drafts"] }] },
        "/api/user/order-list": { items: [{ order_id: "ORD-1", package_type: "monthly", total_amount: 2900, payment_status: "paid", payment_channel: "demo", create_time: "2026-08-19T00:00:00+00:00", entitlement_expire_time: null }] },
        "/api/pay/callback": { order: { order_id: "ORD-1", package_type: "monthly", total_amount: 2900, payment_status: "paid", payment_channel: "demo", create_time: "2026-08-19T00:00:00+00:00", entitlement_expire_time: null }, vip: { vip_level: "basic", expire_time: null, auto_renew: false } },
      }
      return { statusCode: 200, data: { code: "ok", data: dataByPath[options.url], message: "" } }
    },
  }
})

describe("Phase6 account, collection, and membership services", () => {
  it("maps account scope and deletion acknowledgements", async () => {
    await expect(requestAccountScope()).resolves.toEqual({ categories: ["resume_drafts"], retentionNote: "Acknowledgement only" })
    await expect(requestAccountDeletion()).resolves.toEqual({ status: "requested", message: "No account data has been deleted." })
  })

  it("maps favorites and persists the requested subscription state", async () => {
    await expect(listFavoriteJobs()).resolves.toEqual([{
      id: "fav-1", roleName: "Data Engineer", note: "Review", createdAt: "2026-08-19T00:00:00+00:00",
    }])
    await expect(setJobMatchSubscription(true)).resolves.toBe(true)
    expect(calls.at(-1)).toMatchObject({ url: "/api/job-collection/subscription", method: "PUT", data: { enabled: true } })
  })

  it("maps existing membership packages, orders, and the demo payment callback", async () => {
    await expect(listMembershipPackages()).resolves.toEqual([{
      packageType: "monthly", name: "Monthly", vipLevel: "basic", durationDays: 30, totalAmount: 2900, benefits: ["Drafts"],
    }])
    await expect(listOrders()).resolves.toHaveLength(1)
    await expect(completeDemoPayment("ORD-1")).resolves.toMatchObject({ order: { orderId: "ORD-1" }, vip: { vipLevel: "basic" } })
    expect(calls.at(-1)).toMatchObject({ url: "/api/pay/callback", method: "POST", data: { order_id: "ORD-1", payment_channel: "demo", payment_status: "paid" } })
  })
})
