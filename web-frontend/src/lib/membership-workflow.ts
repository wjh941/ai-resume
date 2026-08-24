import type { MembershipOrder } from "./membership"

export function prependOrder(items: MembershipOrder[], order: MembershipOrder): MembershipOrder[] {
  return [order, ...items]
}

export function replaceOrder(items: MembershipOrder[], updated: MembershipOrder): MembershipOrder[] {
  return items.map((item) => item.orderId === updated.orderId ? updated : item)
}
