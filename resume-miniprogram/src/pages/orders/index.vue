<script setup lang="ts">
import { onMounted, ref } from "vue"

import { listOrders, type MembershipOrder } from "../../services/membership-api"
import { toUserMessage } from "../../services/http"

const orders = ref<MembershipOrder[]>([])
const loading = ref(false)
const error = ref("")

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    orders.value = await listOrders()
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to load order history.")
  } finally {
    loading.value = false
  }
}

onMounted(() => { void load() })
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="hero"><text class="eyebrow">ORDERS</text><text class="title">Membership order history</text><text class="copy">Demo orders are retained here for the signed-in account.</text></view>
    <text v-if="loading" class="notice">Loading order history...</text>
      <text v-else-if="error" class="ui-error-tip">{{ error }}</text>
    <view v-for="item in orders" :key="item.orderId" class="order-card"><view><text class="order-id">{{ item.orderId }}</text><text class="copy">{{ item.packageType }} · {{ item.paymentStatus }} · {{ item.createTime }}</text></view><text class="amount">{{ (item.totalAmount / 100).toFixed(2) }}</text></view>
    <view v-if="!loading && !error && !orders.length" class="empty-state"><view class="empty-illustration"><view></view><view></view><view></view></view><text>No membership orders yet</text></view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; box-sizing: border-box; padding: 28rpx; background: #f4f7fb; }.hero,.order-card { padding: 26rpx; background: #fff; border: 1rpx solid #e1eaf4; border-radius: 18rpx; box-shadow: 0 8rpx 22rpx rgba(35, 78, 130, .06); }.eyebrow,.title,.copy,.notice,.error,.order-id,.amount,.empty-state > text { display: block; }.eyebrow { color: #1677ff; font-size: 21rpx; font-weight: 700; }.title { margin-top: 10rpx; color: #1f2937; font-size: 38rpx; font-weight: 700; }.copy { margin-top: 10rpx; color: #64748b; font-size: 23rpx; line-height: 1.55; }.notice,.error { margin-top: 22rpx; text-align: center; font-size: 24rpx; }.notice { color: #64748b; }.error { color: #c2410c; }.order-card { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; margin-top: 16rpx; }.order-id { color: #334155; font-size: 27rpx; font-weight: 700; }.amount { flex-shrink: 0; color: #1677ff; font-size: 30rpx; font-weight: 700; }.empty-state { margin-top: 40rpx; color: #64748b; font-size: 25rpx; text-align: center; }.empty-illustration { display: flex; flex-direction: column; gap: 8rpx; width: 110rpx; margin: 0 auto 18rpx; padding: 18rpx; background: #eef6ff; border: 1rpx solid #d4e8ff; border-radius: 16rpx; }.empty-illustration view { height: 9rpx; background: #9fc8f7; border-radius: 999rpx; }.empty-illustration view:nth-child(2) { width: 75%; }.empty-illustration view:nth-child(3) { width: 50%; }
</style>
