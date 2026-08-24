<script setup lang="ts">
import { onMounted, ref } from "vue"

import LoadingSpinner from "../../components/LoadingSpinner.vue"
import {
  completeDemoPayment,
  createMembershipOrder,
  getVipStatus,
  listMembershipPackages,
  listOrders,
  type MembershipOrder,
  type MembershipPackage,
  type VipStatus,
} from "../../services/membership-api"
import { toUserMessage } from "../../services/http"

const vip = ref<VipStatus | null>(null)
const packages = ref<MembershipPackage[]>([])
const pendingOrder = ref<MembershipOrder | null>(null)
const orders = ref<MembershipOrder[]>([])
const loading = ref(false)
const purchasing = ref(false)
const error = ref("")

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    const [status, items, history] = await Promise.all([getVipStatus(), listMembershipPackages(), listOrders()])
    vip.value = status
    packages.value = items
    orders.value = history
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to load membership options.")
  } finally {
    loading.value = false
  }
}

async function beginDemoCheckout(item: MembershipPackage): Promise<void> {
  purchasing.value = true
  error.value = ""
  try {
    pendingOrder.value = await createMembershipOrder(item.packageType)
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to create a demo order.")
  } finally {
    purchasing.value = false
  }
}

async function completeCheckout(): Promise<void> {
  if (!pendingOrder.value) return
  purchasing.value = true
  try {
    const result = await completeDemoPayment(pendingOrder.value.orderId)
    vip.value = result.vip
    pendingOrder.value = null
    orders.value = await listOrders()
    uni.showToast({ title: "Demo payment completed", icon: "success" })
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to complete the demo payment.")
  } finally {
    purchasing.value = false
  }
}

onMounted(() => { void load() })
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="status-card"><text class="eyebrow">MEMBERSHIP</text><text class="title">{{ vip?.vipLevel || "Loading" }} plan</text><text class="copy">{{ vip?.expireTime ? `Valid until ${vip.expireTime}` : "No active paid entitlement" }}</text><text class="copy">{{ vip?.autoRenew ? "Auto-renew preference is on" : "Auto-renew preference is off" }}</text></view>
    <view v-if="pendingOrder" class="demo-card"><text class="section-title">Demo checkout ready</text><text class="copy">Order {{ pendingOrder.orderId }} was created. Real payment gateways are intentionally not connected.</text><button class="primary" :loading="purchasing" :disabled="purchasing" @click="completeCheckout">Complete demo payment</button></view>
    <text v-if="error" class="error">{{ error }}</text>
    <view v-if="loading" class="notice"><LoadingSpinner size="sm" label="Loading membership options" /><text>Loading membership options...</text></view>
    <view v-for="item in packages" :key="item.packageType" class="package-card"><text class="package-name">{{ item.name }}</text><text class="price">{{ (item.totalAmount / 100).toFixed(2) }}</text><text v-for="benefit in item.benefits" :key="benefit" class="benefit">{{ benefit }}</text><button :loading="purchasing" :disabled="purchasing" @click="beginDemoCheckout(item)">Create demo order</button></view>
    <view v-if="orders.length" class="history"><text class="section-title">Recent orders</text><view v-for="item in orders.slice(0, 3)" :key="item.orderId" class="history-row"><text>{{ item.packageType }} - {{ item.paymentStatus }}</text><text>{{ item.createTime }}</text></view></view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; box-sizing: border-box; padding: 28rpx; background: #f4f7fb; }.status-card,.demo-card,.package-card { margin-top: 20rpx; padding: 26rpx; background: #fff; border: 1rpx solid #e1eaf4; border-radius: 18rpx; box-shadow: 0 8rpx 22rpx rgba(35, 78, 130, .06); }.status-card { margin-top: 0; }.eyebrow,.title,.copy,.section-title,.error,.notice,.package-name,.price,.benefit { display: block; }.eyebrow { color: #1677ff; font-size: 21rpx; font-weight: 700; }.title { margin-top: 10rpx; color: #1f2937; font-size: 38rpx; font-weight: 700; text-transform: capitalize; }.copy { margin-top: 10rpx; color: #64748b; font-size: 23rpx; line-height: 1.55; }.section-title,.package-name { color: #334155; font-size: 29rpx; font-weight: 700; }.package-card { border-color: #dbe9f8; }.price { margin-top: 12rpx; color: #1677ff; font-size: 40rpx; font-weight: 700; }.benefit { margin-top: 10rpx; color: #52677d; font-size: 23rpx; }.package-card button,.demo-card button { margin-top: 20rpx; color: #245b99; background: #edf6ff; border: 1rpx solid #cfe4fb; font-size: 24rpx; }.primary { color: #fff !important; background: #1677ff !important; border-color: #1677ff !important; }.error,.notice { margin-top: 18rpx; font-size: 24rpx; text-align: center; }.error { color: #c2410c; }.notice { color: #64748b; }.history { margin-top: 24rpx; }.history-row { display: flex; justify-content: space-between; gap: 16rpx; padding: 16rpx 0; color: #52677d; border-bottom: 1rpx solid #e1eaf4; font-size: 22rpx; }.history-row text { min-width: 0; overflow-wrap: anywhere; }
</style>
