<script setup lang="ts">
import { ref } from "vue"

import { loginPhone, sendPhoneCode } from "../../services/auth-api"
import { toUserMessage } from "../../services/http"
import { setAuthSession } from "../../stores/session"

const phone = ref("")
const code = ref("")
const sending = ref(false)
const loggingIn = ref(false)
const hint = ref("")
const error = ref("")

function validPhone(value: string): boolean {
  return /^1[3-9]\d{9}$/.test(value.trim())
}

async function requestCode(): Promise<void> {
  const normalized = phone.value.trim()
  if (!validPhone(normalized)) {
    error.value = "Enter a valid mobile number."
    return
  }
  sending.value = true
  error.value = ""
  try {
    const result = await sendPhoneCode(normalized)
    hint.value = result.demoCode ? `Development code: ${result.demoCode}` : result.message
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to request a verification code.")
  } finally {
    sending.value = false
  }
}

async function signIn(): Promise<void> {
  const normalized = phone.value.trim()
  if (!validPhone(normalized) || !code.value.trim()) {
    error.value = "Enter your mobile number and verification code."
    return
  }
  loggingIn.value = true
  error.value = ""
  try {
    const session = await loginPhone(normalized, code.value.trim())
    setAuthSession(session.token, session.user)
    uni.reLaunch({ url: "/pages/job-search/index" })
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to sign in. Please try again.")
  } finally {
    loggingIn.value = false
  }
}
</script>

<template>
  <view class="page">
    <view class="login-card">
      <text class="eyebrow">AI RESUME</text>
      <text class="title">Sign in to your workspace</text>
      <text class="copy">Your resume drafts, plans, and account controls are protected by your phone session.</text>
      <view class="field"><text>Mobile number</text><input v-model="phone" type="number" maxlength="11" placeholder="13800138000" /></view>
      <view class="field code-field"><text>Verification code</text><input v-model="code" type="number" maxlength="6" placeholder="123456" /><button :loading="sending" @click="requestCode">Get code</button></view>
      <text v-if="hint" class="hint">{{ hint }}</text>
      <text v-if="error" class="error">{{ error }}</text>
      <button class="primary" :loading="loggingIn" @click="signIn">Sign in</button>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; box-sizing: border-box; padding: 64rpx 28rpx; background: #f4f7fb; }.login-card { max-width: 620rpx; margin: 0 auto; padding: 38rpx 30rpx; background: #fff; border: 1rpx solid #e1eaf4; border-radius: 20rpx; box-shadow: 0 12rpx 30rpx rgba(35, 78, 130, .09); }.eyebrow,.title,.copy,.field > text,.hint,.error { display: block; }.eyebrow { color: #1677ff; font-size: 21rpx; font-weight: 700; }.title { margin-top: 12rpx; color: #1f2937; font-size: 40rpx; font-weight: 700; }.copy { margin-top: 14rpx; color: #64748b; font-size: 25rpx; line-height: 1.6; }.field { margin-top: 26rpx; }.field > text { margin-bottom: 10rpx; color: #4b5563; font-size: 24rpx; }.field input { width: 100%; min-height: 78rpx; box-sizing: border-box; padding: 0 18rpx; background: #f8fafc; border: 1rpx solid #dfe7f1; border-radius: 12rpx; font-size: 27rpx; }.code-field { display: grid; grid-template-columns: 1fr auto; gap: 12rpx; }.code-field > text { grid-column: 1 / -1; }.code-field button { margin: 0; padding: 0 20rpx; color: #1677ff; background: #edf6ff; border: 1rpx solid #b7d8ff; font-size: 23rpx; }.hint,.error { margin-top: 14rpx; font-size: 23rpx; line-height: 1.5; }.hint { color: #26735c; }.error { color: #c2410c; }.primary { margin-top: 28rpx; color: #fff; background: #1677ff; }
</style>
