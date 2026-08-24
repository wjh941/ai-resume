<script setup lang="ts">
import { CheckCircle2, Crown, RefreshCw } from "lucide-vue-next"
import { onMounted, ref } from "vue"

import AsyncButton from "../components/AsyncButton.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import MembershipPackageCard from "../components/MembershipPackageCard.vue"
import OrderRow from "../components/OrderRow.vue"
import { completeDemoPayment, createMembershipOrder, getVipStatus, listMembershipPackages, listOrders, type MembershipOrder, type MembershipPackage, type VipStatus } from "../lib/membership"
import { prependOrder, replaceOrder } from "../lib/membership-workflow"

const vip = ref<VipStatus | null>(null)
const packages = ref<MembershipPackage[]>([])
const orders = ref<MembershipOrder[]>([])
const loading = ref(true)
const error = ref("")
const notice = ref("")
const pendingPackage = ref("")
const payingOrderId = ref("")
const phase = ref<"idle" | "creating" | "awaiting-payment" | "paying" | "paid" | "error">("idle")
const pendingOrder = ref<MembershipOrder | null>(null)

async function refresh(): Promise<void> {
  loading.value = true; error.value = ""
  try { const [currentVip, available, orderList] = await Promise.all([getVipStatus(), listMembershipPackages(), listOrders()]); vip.value = currentVip; packages.value = available; orders.value = orderList; phase.value = "idle" } catch { error.value = "暂时无法读取会员信息，请稍后重试" } finally { loading.value = false }
}
async function purchase(packageType: MembershipPackage["packageType"], autoRenew: boolean): Promise<void> {
  if (pendingPackage.value) return
  pendingPackage.value = packageType; phase.value = "creating"; error.value = ""; notice.value = ""
  try { pendingOrder.value = await createMembershipOrder(packageType, autoRenew); orders.value = prependOrder(orders.value, pendingOrder.value); phase.value = "awaiting-payment"; notice.value = "订单已创建，确认后再完成支付" } catch (caught) { phase.value = "error"; error.value = caught instanceof Error ? caught.message : "订单暂未创建，请稍后重试" } finally { pendingPackage.value = "" }
}
async function payDemo(): Promise<void> {
  if (!pendingOrder.value || payingOrderId.value) return
  payingOrderId.value = pendingOrder.value.orderId; phase.value = "paying"; error.value = ""
  try { const result = await completeDemoPayment(pendingOrder.value.orderId); vip.value = result.vip; orders.value = replaceOrder(orders.value, result.order); pendingOrder.value = null; phase.value = "paid"; notice.value = "支付已确认，会员权益已刷新" } catch (caught) { phase.value = "error"; error.value = caught instanceof Error ? caught.message : "支付暂未完成，请稍后重试" } finally { payingOrderId.value = "" }
}
onMounted(refresh)
</script>

<template>
  <section class="view-layout membership-view">
    <div class="view-heading"><div><h1 id="membership-title">会员与订单</h1><p>查看当前权益、选择服务套餐，并保留完整的订单状态。</p></div><AsyncButton class="text-action" type="button" :loading="loading" @click="refresh"><RefreshCw :size="16" aria-hidden="true" />刷新</AsyncButton></div>
    <p v-if="error" class="notice-error" role="alert">{{ error }}</p><p v-if="notice" class="notice-success" aria-live="polite"><CheckCircle2 :size="16" aria-hidden="true" />{{ notice }}</p>
    <div v-if="loading" class="content-skeleton membership-loading" aria-busy="true"><LoadingSpinner class="content-loading-spinner" label="正在读取会员信息" /><span /><span /><span /></div>
    <template v-else>
      <section class="membership-entitlement"><div class="record-symbol record-coral"><Crown :size="24" aria-hidden="true" /></div><div><span class="section-kicker">当前权益</span><h2>{{ vip?.vipLevel || "普通用户" }}</h2><p>到期时间：{{ vip?.expireTime || "暂无到期时间" }} · {{ vip?.autoRenew ? "已开启自动续费" : "未开启自动续费" }}</p></div></section>
      <section class="membership-packages"><div class="panel-heading"><div><span class="section-kicker">服务套餐</span><h2>选择适合你的成长节奏</h2></div></div><div class="package-grid"><MembershipPackageCard v-for="item in packages" :key="item.packageType" :package="item" :current-vip="vip" :pending="pendingPackage === item.packageType" @purchase="purchase" /></div></section>
      <section v-if="phase === 'awaiting-payment' && pendingOrder" class="payment-pending"><div><h2>订单待支付</h2><p>{{ pendingOrder.orderId }} · ¥{{ pendingOrder.totalAmount }} · 当前状态：{{ pendingOrder.paymentStatus }}</p></div><AsyncButton class="primary-button compact" type="button" :loading="phase === 'paying'" @click="payDemo">完成演示支付</AsyncButton></section>
      <section v-if="phase === 'paid'" class="notice-success"><CheckCircle2 :size="17" aria-hidden="true" />订单已支付，权益状态已更新。</section>
      <section class="order-panel"><div class="panel-heading"><div><span class="section-kicker">订单记录</span><h2>支付状态</h2></div></div><div v-if="orders.length" class="order-list"><OrderRow v-for="order in orders" :key="order.orderId" :order="order" /></div><p v-else class="source-notice">还没有订单记录。</p></section>
    </template>
  </section>
</template>
