<script setup lang="ts">
import { computed, onMounted, ref } from "vue"

import { getCurrentUser, logout } from "../../services/auth-api"
import { recordPrivacyConsent, requestAccountDataExport, requestAccountDeletion, requestAccountPrivacyDetails, type AccountPrivacyDetails } from "../../services/account-api"
import { apiUrl, toUserMessage } from "../../services/http"
import { clearAuthSession, getAuthToken, getAuthUser } from "../../stores/session"
import type { AuthUser } from "../../types/auth"

const user = ref<AuthUser | null>(getAuthUser())
const loading = ref(false)
const error = ref("")
const dataScope = ref<AccountPrivacyDetails | null>(null)
const lifecycleMessage = ref("")
const consentRecorded = ref(false)
const isOperator = computed(() => user.value?.role === "operator")

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
    error.value = toUserMessage(reason, "无法加载账户信息，请稍后重试。")
  } finally {
    loading.value = false
  }
}

function signOut(): void {
  uni.showModal({
    title: "退出登录",
    content: "确定退出当前设备吗？下次登录后仍可继续使用已保存的数据。",
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
    dataScope.value = await requestAccountPrivacyDetails()
  } catch (reason) {
    error.value = toUserMessage(reason, "无法加载数据范围，请稍后重试。")
  }
}

async function requestDataExport(): Promise<void> {
  try {
    const result = await requestAccountDataExport()
    lifecycleMessage.value = result.message
    uni.downloadFile({
      url: apiUrl(result.downloadUrl),
      header: getAuthToken() ? { Authorization: `Bearer ${getAuthToken()}` } : {},
      success: () => { lifecycleMessage.value = "ZIP 数据导出已开始下载。" },
      fail: () => { lifecycleMessage.value = "导出文件已准备完成，但当前设备下载失败，请重试。" },
    })
  } catch (reason) {
    error.value = toUserMessage(reason, "无法创建数据导出，请稍后重试。")
  }
}

async function acknowledgePrivacyPolicy(): Promise<void> {
  try {
    await recordPrivacyConsent()
    consentRecorded.value = true
    lifecycleMessage.value = "已记录隐私政策确认。"
  } catch (reason) {
    error.value = toUserMessage(reason, "无法记录隐私偏好，请稍后重试。")
  }
}

function requestDeletion(): void {
  uni.showModal({
    title: "申请注销账户",
    content: "确认后将退出登录，并匿名化简历与职业规划数据。此操作无法撤销。",
    success: async (result) => {
      if (!result.confirm) return
      try {
        lifecycleMessage.value = (await requestAccountDeletion()).message
      } catch (reason) {
        error.value = toUserMessage(reason, "无法提交注销申请，请稍后重试。")
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
      <text class="title">账户中心</text>
      <text class="meta">{{ user?.phone || "需要登录后查看" }}</text>
      <text class="meta">{{ loading ? "正在刷新账户信息…" : user ? `账户标识：${user.userId}` : "当前登录状态不可用。" }}</text>
      <text v-if="error" class="error">{{ error }}</text>
    </view>
    <view class="section">
      <text class="section-title">我的工作台</text>
      <button @click="open('/pages/drafts/index')">简历草稿</button>
      <button @click="open('/pages/privacy/index')">本地隐私</button>
      <button @click="open('/pages/job-collection/index')">收藏岗位与订阅</button>
      <button @click="open('/pages/membership/index')">会员服务</button>
      <button @click="open('/pages/orders/index')">订单记录</button>
      <button v-if="isOperator" @click="open('/pages/operator-knowledge/index')">运营知识库</button>
    </view>
    <view class="section">
      <text class="section-title">账户数据范围</text>
      <text class="scope-copy">{{ dataScope?.categories.join("、") || "正在加载数据范围…" }}</text>
      <text class="scope-copy">{{ dataScope?.retentionNote }}</text>
      <text class="policy-hint">{{ dataScope?.privacyPolicyHint }}</text>
      <button :disabled="consentRecorded" @click="acknowledgePrivacyPolicy">{{ consentRecorded ? "已确认隐私政策" : "确认隐私政策" }}</button>
      <button @click="requestDataExport">导出我的数据</button>
      <button class="danger-inline" @click="requestDeletion">申请注销账户</button>
      <text v-if="lifecycleMessage" class="acknowledgement">{{ lifecycleMessage }}</text>
    </view>
    <button class="danger" @click="signOut">退出登录</button>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; box-sizing: border-box; padding: 28rpx; background: #f4f7fb; }.profile-card,.section { padding: 26rpx; background: #fff; border: 1rpx solid #e1eaf4; border-radius: 18rpx; box-shadow: 0 8rpx 22rpx rgba(35, 78, 130, .06); }.title,.meta,.section-title,.error,.scope-copy,.policy-hint,.acknowledgement { display: block; }.title { color: #1f2937; font-size: 38rpx; font-weight: 700; }.meta { margin-top: 10rpx; color: #718096; font-size: 23rpx; word-break: break-all; }.error { margin-top: 12rpx; color: #c2410c; font-size: 23rpx; }.section { margin-top: 20rpx; }.section-title { color: #334155; font-size: 29rpx; font-weight: 700; }.section button { margin-top: 14rpx; color: #245b99; background: #edf6ff; border: 1rpx solid #cfe4fb; text-align: left; font-size: 25rpx; }.scope-copy,.policy-hint { margin-top: 10rpx; color: #64748b; font-size: 23rpx; line-height: 1.55; }.policy-hint { color: #3b6389; overflow-wrap: anywhere; }.danger-inline { color: #c2410c !important; background: #fff7f0 !important; border-color: #ffccc7 !important; }.acknowledgement { margin-top: 14rpx; color: #26735c; font-size: 23rpx; }.danger { margin-top: 24rpx; color: #c2410c; background: #fff7f0; border: 1rpx solid #ffccc7; }
</style>
