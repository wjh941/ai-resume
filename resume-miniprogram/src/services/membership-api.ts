import { request } from "./http"

export type VipStatus = {
  vipLevel: string
  expireTime: string | null
  autoRenew: boolean
}

export type MembershipPackage = {
  packageType: "monthly" | "quarterly" | "annual"
  name: string
  vipLevel: string
  durationDays: number
  totalAmount: number
  benefits: string[]
}

export type MembershipOrder = {
  orderId: string
  packageType: string
  totalAmount: number
  paymentStatus: string
  paymentChannel: string | null
  createTime: string
  entitlementExpireTime: string | null
}

type BackendVip = { vip_level: string; expire_time: string | null; auto_renew: boolean }
type BackendPackage = { package_type: MembershipPackage["packageType"]; name: string; vip_level: string; duration_days: number; total_amount: number; benefits: string[] }
type BackendOrder = { order_id: string; package_type: string; total_amount: number; payment_status: string; payment_channel: string | null; create_time: string; entitlement_expire_time: string | null }

const mapVip = (item: BackendVip): VipStatus => ({ vipLevel: item.vip_level, expireTime: item.expire_time, autoRenew: item.auto_renew })
const mapPackage = (item: BackendPackage): MembershipPackage => ({ packageType: item.package_type, name: item.name, vipLevel: item.vip_level, durationDays: item.duration_days, totalAmount: item.total_amount, benefits: item.benefits })
const mapOrder = (item: BackendOrder): MembershipOrder => ({ orderId: item.order_id, packageType: item.package_type, totalAmount: item.total_amount, paymentStatus: item.payment_status, paymentChannel: item.payment_channel, createTime: item.create_time, entitlementExpireTime: item.entitlement_expire_time })

export async function getVipStatus(): Promise<VipStatus> {
  return mapVip(await request<BackendVip>("/api/user/vip-info"))
}

export async function listMembershipPackages(): Promise<MembershipPackage[]> {
  const data = await request<{ items: BackendPackage[] }>("/api/pay/package-list")
  return data.items.map(mapPackage)
}

export async function createMembershipOrder(packageType: MembershipPackage["packageType"], autoRenew = false): Promise<MembershipOrder> {
  return mapOrder(await request<BackendOrder>("/api/pay/create-order", "POST", { package_type: packageType, auto_renew: autoRenew }))
}

export async function completeDemoPayment(orderId: string): Promise<{ order: MembershipOrder; vip: VipStatus }> {
  const data = await request<{ order: BackendOrder; vip: BackendVip }>("/api/pay/callback", "POST", {
    order_id: orderId,
    payment_channel: "demo",
    payment_status: "paid",
  })
  return { order: mapOrder(data.order), vip: mapVip(data.vip) }
}

export async function listOrders(): Promise<MembershipOrder[]> {
  const data = await request<{ items: BackendOrder[] }>("/api/user/order-list")
  return data.items.map(mapOrder)
}
