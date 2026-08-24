<script setup lang="ts">
import { ref } from "vue"

import { loginPasswordAccount, loginPhone, registerPasswordAccount, sendPhoneCode } from "../../services/auth-api"
import { toUserMessage } from "../../services/http"
import { setAuthSession } from "../../stores/session"

const phone = ref("")
const code = ref("")
const account = ref("")
const password = ref("")
const loginMode = ref<"phone" | "password">("phone")
const sending = ref(false)
const loggingIn = ref(false)
const passwordAction = ref<"login" | "register" | null>(null)
const hint = ref("")
const error = ref("")

function validPhone(value: string): boolean {
  return /^1[3-9]\d{9}$/.test(value.trim())
}

function validAccount(value: string): boolean {
  return /^[a-z][a-z0-9_.-]{2,31}$/.test(value.trim().toLowerCase())
}

function validPassword(value: string): boolean {
  return value.length >= 10 && value.length <= 72
}

function changeLoginMode(mode: "phone" | "password"): void {
  if (sending.value || loggingIn.value || passwordAction.value !== null) return
  loginMode.value = mode
  hint.value = ""
  error.value = ""
}

async function requestCode(): Promise<void> {
  if (sending.value || loggingIn.value || passwordAction.value !== null) return
  const normalized = phone.value.trim()
  if (!validPhone(normalized)) {
    error.value = "请输入正确的手机号。"
    return
  }
  sending.value = true
  error.value = ""
  try {
    const result = await sendPhoneCode(normalized)
    hint.value = result.demoCode ? `开发环境验证码：${result.demoCode}` : result.message
  } catch (reason) {
    error.value = toUserMessage(reason, "无法获取验证码，请稍后重试。")
  } finally {
    sending.value = false
  }
}

async function signIn(): Promise<void> {
  if (sending.value || loggingIn.value || passwordAction.value !== null) return
  const normalized = phone.value.trim()
  if (!validPhone(normalized) || !code.value.trim()) {
    error.value = "请输入手机号和验证码。"
    return
  }
  loggingIn.value = true
  error.value = ""
  try {
    const session = await loginPhone(normalized, code.value.trim())
    setAuthSession(session.token, session.user)
    uni.reLaunch({ url: "/pages/job-search/index" })
  } catch (reason) {
    error.value = toUserMessage(reason, "登录失败，请稍后重试。")
  } finally {
    loggingIn.value = false
  }
}

async function submitPassword(action: "login" | "register"): Promise<void> {
  if (sending.value || loggingIn.value || passwordAction.value !== null) return
  const normalized = account.value.trim().toLowerCase()
  if (!validAccount(normalized)) {
    error.value = "账号需为 3-32 位小写英文字母、数字或 ._-。"
    return
  }
  if (!validPassword(password.value)) {
    error.value = "密码长度需为 10-72 个字符。"
    return
  }
  passwordAction.value = action
  error.value = ""
  try {
    const session = action === "register"
      ? await registerPasswordAccount(normalized, password.value)
      : await loginPasswordAccount(normalized, password.value)
    setAuthSession(session.token, session.user)
    uni.reLaunch({ url: "/pages/job-search/index" })
  } catch (reason) {
    error.value = toUserMessage(reason, action === "register" ? "注册失败，请稍后重试。" : "登录失败，请稍后重试。")
  } finally {
    passwordAction.value = null
  }
}

function showWechatSetup(): void {
  uni.showModal({
    title: "微信登录暂不可用",
    content: "微信 OAuth 需要在微信开放平台配置已备案的 HTTPS 回调域名，当前环境尚未启用。",
    showCancel: false,
  })
}
</script>

<template>
  <view class="page">
    <view class="login-card">
      <text class="title">登录你的求职工作台</text>
      <text class="copy">登录后可安全访问你的简历草稿、职业计划和账户设置。</text>
      <view class="auth-tabs" role="tablist">
        <button class="tab" :class="{ active: loginMode === 'phone' }" :disabled="Boolean(sending || loggingIn || passwordAction)" @click="changeLoginMode('phone')">手机号验证码</button>
        <button class="tab" :class="{ active: loginMode === 'password' }" :disabled="Boolean(sending || loggingIn || passwordAction)" @click="changeLoginMode('password')">账号密码</button>
      </view>
      <template v-if="loginMode === 'phone'">
        <view class="field"><text>手机号</text><input v-model="phone" type="number" maxlength="11" placeholder="13800138000" /></view>
        <view class="field code-field"><text>验证码</text><input v-model="code" type="number" maxlength="6" placeholder="123456" /><button :loading="sending" :disabled="sending || loggingIn" @click="requestCode">获取验证码</button></view>
        <text v-if="hint" class="hint">{{ hint }}</text>
      </template>
      <template v-else>
        <view class="field"><text>账号</text><input v-model="account" maxlength="32" placeholder="例如：career_owner" /></view>
        <view class="field"><text>密码</text><input v-model="password" password maxlength="72" placeholder="10-72 个字符" /></view>
        <text class="field-hint">账号仅支持小写英文字母、数字和 ._-；密码至少 10 个字符。</text>
      </template>
      <text v-if="error" class="error">{{ error }}</text>
      <button v-if="loginMode === 'phone'" class="primary" :loading="loggingIn" :disabled="loggingIn || sending" @click="signIn">登录</button>
      <template v-else>
        <button class="primary" :loading="passwordAction === 'login'" :disabled="passwordAction !== null || sending || loggingIn" @click="submitPassword('login')">账号登录</button>
        <button class="secondary" :loading="passwordAction === 'register'" :disabled="passwordAction !== null || sending || loggingIn" @click="submitPassword('register')">注册新账号</button>
      </template>
      <button class="wechat" @click="showWechatSetup">微信登录</button>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; box-sizing: border-box; padding: 64rpx 28rpx; background: #f4f7fb; }.login-card { max-width: 620rpx; margin: 0 auto; padding: 38rpx 30rpx; background: #fff; border: 1rpx solid #e1eaf4; border-radius: 12rpx; box-shadow: 0 12rpx 30rpx rgba(35, 78, 130, .09); }.title,.copy,.field > text,.hint,.error,.field-hint { display: block; }.title { color: #1f2937; font-size: 40rpx; font-weight: 700; }.copy { margin-top: 14rpx; color: #64748b; font-size: 25rpx; line-height: 1.6; }.auth-tabs { display: grid; grid-template-columns: 1fr 1fr; gap: 8rpx; margin-top: 26rpx; padding: 6rpx; background: #edf3fa; border-radius: 10rpx; }.tab { min-width: 0; margin: 0; padding: 16rpx 10rpx; color: #52657c; background: transparent; border: 0; border-radius: 8rpx; font-size: 25rpx; line-height: 1.35; }.tab.active { color: #0f5fbf; background: #fff; box-shadow: 0 2rpx 8rpx rgba(35, 78, 130, .12); }.field { margin-top: 26rpx; }.field > text { margin-bottom: 10rpx; color: #4b5563; font-size: 24rpx; }.field input { width: 100%; min-height: 78rpx; box-sizing: border-box; padding: 0 18rpx; background: #f8fafc; border: 1rpx solid #dfe7f1; border-radius: 10rpx; font-size: 28rpx; }.code-field { display: grid; grid-template-columns: 1fr auto; gap: 12rpx; }.code-field > text { grid-column: 1 / -1; }.code-field button { margin: 0; padding: 0 20rpx; color: #1677ff; background: #edf6ff; border: 1rpx solid #b7d8ff; font-size: 23rpx; }.field-hint,.hint,.error { margin-top: 14rpx; font-size: 23rpx; line-height: 1.5; }.field-hint { color: #64748b; }.hint { color: #26735c; }.error { color: #c2410c; }.primary { margin-top: 28rpx; color: #fff; background: #1677ff; }.secondary,.wechat { margin-top: 14rpx; color: #245b99; background: #edf6ff; border: 1rpx solid #cfe4fb; }.wechat { margin-top: 14rpx; }
.login-card { border-radius: var(--ui-card-radius); }
.auth-tabs { border-radius: var(--ui-control-radius); }
.tab { transition: color var(--ui-motion-fast) var(--ui-motion-ease), background-color var(--ui-motion-fast) var(--ui-motion-ease), box-shadow var(--ui-motion-fast) var(--ui-motion-ease); }
.tab.active { transform: translateY(-1rpx); }
.field input { border-radius: var(--ui-control-radius); transition: border-color var(--ui-motion-fast) var(--ui-motion-ease), box-shadow var(--ui-motion-fast) var(--ui-motion-ease); }
.field input:focus { border-color: #8ebeff; box-shadow: 0 0 0 4rpx rgba(22, 119, 255, .12); }
@media (prefers-reduced-motion: reduce) { .tab,.field input { transition: none; }.tab.active { transform: none; } }
</style>
