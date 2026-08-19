<script setup lang="ts">
import { onMounted, ref } from "vue"

import { getCurrentUser, logout } from "../../services/auth-api"
import { requestAccountDataExport, requestAccountDeletion, requestAccountScope, type AccountDataScope } from "../../services/account-api"
import { toUserMessage } from "../../services/http"
import { clearAuthSession, getAuthUser } from "../../stores/session"
import type { AuthUser } from "../../types/auth"

const user = ref<AuthUser | null>(getAuthUser())
const loading = ref(false)
const error = ref("")
const dataScope = ref<AccountDataScope | null>(null)
const lifecycleMessage = ref("")

async function loadUser(): Promise<void> {
  if (!user.value) {
    uni.reLaunch({ url: "/pages/login/index" })
    return
  }
  loading.value = true
  error.value = ""
  try {
    user.value = await getCurrentUser()
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to load your account.")
  } finally {
    loading.value = false
  }
}

function signOut(): void {
  uni.showModal({
    title: "Sign out",
    content: "Sign out from this device? Your server records will remain available next time you sign in.",
    success: async (result) => {
      if (!result.confirm) return
      try {
        await logout()
      } finally {
        clearAuthSession()
        uni.reLaunch({ url: "/pages/login/index" })
      }
    },
  })
}

function open(path: string): void {
  uni.navigateTo({ url: path })
}

async function loadScope(): Promise<void> {
  try {
    dataScope.value = await requestAccountScope()
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to load account privacy details.")
  }
}

async function requestDataExport(): Promise<void> {
  try {
    lifecycleMessage.value = (await requestAccountDataExport()).message
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to request a data export.")
  }
}

function requestDeletion(): void {
  uni.showModal({
    title: "Request account deletion",
    content: "This development version will only record an acknowledgement. No account data will be deleted.",
    success: async (result) => {
      if (!result.confirm) return
      try {
        lifecycleMessage.value = (await requestAccountDeletion()).message
      } catch (reason) {
        error.value = toUserMessage(reason, "Unable to request account deletion.")
      }
    },
  })
}

onMounted(async () => {
  await loadUser()
  if (user.value) await loadScope()
})
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="profile-card">
      <text class="eyebrow">ACCOUNT</text>
      <text class="title">{{ user?.phone || "Sign in required" }}</text>
      <text class="meta">{{ loading ? "Refreshing account..." : user ? `User ID: ${user.userId}` : "Your session is not available." }}</text>
      <text v-if="error" class="error">{{ error }}</text>
    </view>
    <view class="section">
      <text class="section-title">Workspace</text>
      <button @click="open('/pages/drafts/index')">Resume drafts</button>
      <button @click="open('/pages/privacy/index')">Local privacy</button>
      <button @click="open('/pages/job-collection/index')">Favorite jobs and alerts</button>
      <button @click="open('/pages/membership/index')">Membership</button>
      <button @click="open('/pages/orders/index')">Order history</button>
    </view>
    <view class="section">
      <text class="section-title">Account data scope</text>
      <text class="scope-copy">{{ dataScope?.categories.join(" · ") || "Loading data scope..." }}</text>
      <text class="scope-copy">{{ dataScope?.retentionNote }}</text>
      <button @click="requestDataExport">Request data export</button>
      <button class="danger-inline" @click="requestDeletion">Request account deletion</button>
      <text v-if="lifecycleMessage" class="acknowledgement">{{ lifecycleMessage }}</text>
    </view>
    <button class="danger" @click="signOut">Sign out</button>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; box-sizing: border-box; padding: 28rpx; background: #f4f7fb; }.profile-card,.section { padding: 26rpx; background: #fff; border: 1rpx solid #e1eaf4; border-radius: 18rpx; box-shadow: 0 8rpx 22rpx rgba(35, 78, 130, .06); }.eyebrow,.title,.meta,.section-title,.error,.scope-copy,.acknowledgement { display: block; }.eyebrow { color: #1677ff; font-size: 21rpx; font-weight: 700; }.title { margin-top: 10rpx; color: #1f2937; font-size: 38rpx; font-weight: 700; }.meta { margin-top: 10rpx; color: #718096; font-size: 23rpx; word-break: break-all; }.error { margin-top: 12rpx; color: #c2410c; font-size: 23rpx; }.section { margin-top: 20rpx; }.section-title { color: #334155; font-size: 29rpx; font-weight: 700; }.section button { margin-top: 14rpx; color: #245b99; background: #edf6ff; border: 1rpx solid #cfe4fb; text-align: left; font-size: 25rpx; }.scope-copy { margin-top: 10rpx; color: #64748b; font-size: 23rpx; line-height: 1.55; }.danger-inline { color: #c2410c !important; background: #fff7f0 !important; border-color: #ffccc7 !important; }.acknowledgement { margin-top: 14rpx; color: #26735c; font-size: 23rpx; }.danger { margin-top: 24rpx; color: #c2410c; background: #fff7f0; border: 1rpx solid #ffccc7; }
</style>
