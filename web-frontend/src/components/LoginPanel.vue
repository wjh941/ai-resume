<script setup lang="ts">
import { ArrowRight, KeyRound, Smartphone } from "lucide-vue-next"
import { computed, inject, ref } from "vue"

import { loginWithPassword, loginWithPhone, registerAccount } from "../lib/auth"
import { requestApi } from "../lib/api"
import { CAPABILITIES_KEY, createCapabilityContext, isCapabilityEnabled } from "../lib/capabilities"
import type { Session } from "../lib/session"
import AsyncButton from "./AsyncButton.vue"

const emit = defineEmits<{
  authenticated: [session: Session]
}>()

const mode = ref<"password" | "phone">("password")
const accountMode = ref<"login" | "register">("login")
const account = ref("")
const password = ref("")
const phone = ref("")
const code = ref("")
const loading = ref(false)
const sending = ref(false)
const hint = ref("")
const error = ref("")
const context = inject(CAPABILITIES_KEY) ?? createCapabilityContext()
const smsLoginEnabled = computed(() => isCapabilityEnabled(context.capabilities.value, "smsLogin"))
const smsLoginNotice = computed(() => context.capabilities.value.smsLogin.notice)

const submitLabel = computed(() => {
  if (mode.value === "phone") return "手机号登录"
  return accountMode.value === "login" ? "登录工作台" : "创建账户"
})

async function sendCode() {
  if (!isCapabilityEnabled(context.capabilities.value, "smsLogin")) {
    error.value = smsLoginNotice.value
    hint.value = smsLoginNotice.value
    return
  }
  if (loading.value || sending.value) return
  if (!/^1\d{10}$/.test(phone.value)) {
    error.value = "请填写正确的 11 位手机号"
    return
  }

  sending.value = true
  error.value = ""
  hint.value = ""
  try {
    const response = await requestApi<{ message?: string; demo_code?: string }>("/api/auth/send-code", {
      method: "POST",
      body: JSON.stringify({ phone: phone.value }),
    })
    hint.value = response.demo_code ? `本地演示验证码：${response.demo_code}` : response.message || "验证码已发送"
  } catch {
    error.value = "验证码暂时无法发送，请使用账号密码登录或稍后重试"
  } finally {
    sending.value = false
  }
}

async function submit() {
  if (loading.value || sending.value) return
  error.value = ""
  hint.value = ""
  if (mode.value === "phone" && !isCapabilityEnabled(context.capabilities.value, "smsLogin")) {
    error.value = smsLoginNotice.value
    hint.value = smsLoginNotice.value
    return
  }
  loading.value = true
  try {
    const session = mode.value === "phone"
      ? await loginWithPhone(requestApi, phone.value, code.value)
      : accountMode.value === "register"
        ? await registerAccount(requestApi, account.value, password.value)
        : await loginWithPassword(requestApi, account.value, password.value)
    emit("authenticated", session)
  } catch (reason) {
    error.value = reason instanceof Error && reason.message ? reason.message : "登录未完成，请检查填写内容后重试"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-scene">
    <section class="login-promise" aria-label="产品说明">
      <span class="promise-mark"><KeyRound :size="28" aria-hidden="true" /></span>
      <div>
        <h1>把求职准备，变成今天能完成的行动。</h1>
        <p>整理简历、目标岗位、职业计划和投递记录，让下一步清晰可见。</p>
      </div>
      <ul class="promise-list">
        <li>从已有经历中提取可验证亮点</li>
        <li>围绕目标岗位安排补齐计划</li>
        <li>持续追踪投递与面试节奏</li>
      </ul>
    </section>

    <section class="login-form-area" aria-label="登录或注册">
      <div class="login-form-wrap">
        <div class="login-heading">
          <h2>进入工作台</h2>
          <p>使用手机号或个人账户继续。</p>
        </div>
        <div class="login-tabs" role="tablist" aria-label="登录方式">
          <button type="button" :class="{ 'is-selected': mode === 'password' }" :disabled="loading || sending" role="tab" :aria-selected="mode === 'password'" @click="mode = 'password'">账号密码</button>
          <button type="button" :class="{ 'is-selected': mode === 'phone' }" :disabled="!smsLoginEnabled || loading || sending" role="tab" :aria-selected="mode === 'phone'" @click="mode = 'phone'">手机号验证</button>
        </div>
        <p v-if="!smsLoginEnabled" class="form-hint capability-notice" aria-live="polite">{{ smsLoginNotice }}</p>

        <form class="login-form" :aria-describedby="error ? 'login-error' : undefined" @submit.prevent="submit">
          <template v-if="mode === 'password'">
            <label>账号<input v-model.trim="account" autocomplete="username" minlength="3" maxlength="32" required placeholder="3 至 32 位账号" :aria-invalid="Boolean(error && (account.length < 3 || account.length > 32))" /></label>
            <label>密码<input v-model="password" type="password" autocomplete="current-password" minlength="10" maxlength="72" required placeholder="至少 10 位密码" :aria-invalid="Boolean(error && (password.length < 10 || password.length > 72))" /></label>
            <button class="form-link" type="button" @click="accountMode = accountMode === 'login' ? 'register' : 'login'">
              {{ accountMode === 'login' ? '没有账户？创建账户' : '已有账户？直接登录' }}
            </button>
          </template>
          <template v-else>
            <label>手机号<input v-model.trim="phone" inputmode="numeric" autocomplete="tel" maxlength="11" required placeholder="请输入 11 位手机号" :aria-invalid="Boolean(error && !/^1\d{10}$/.test(phone))" /></label>
            <label>验证码<span class="verification-row"><input v-model.trim="code" inputmode="numeric" autocomplete="one-time-code" maxlength="6" required placeholder="6 位验证码" :aria-invalid="Boolean(error && code.length !== 6)" /><AsyncButton type="button" :loading="sending" :disabled="loading" @click="sendCode">{{ sending ? '发送中' : '获取验证码' }}</AsyncButton></span></label>
          </template>

          <p v-if="hint" class="form-hint" aria-live="polite">{{ hint }}</p>
          <ErrorNotice v-if="error" id="login-error" :message="error" compact />
          <AsyncButton class="primary-button" type="submit" :loading="loading" :disabled="sending">
            <span>{{ loading ? '正在验证' : submitLabel }}</span><ArrowRight :size="18" aria-hidden="true" />
          </AsyncButton>
        </form>
        <p class="login-footnote"><Smartphone :size="15" aria-hidden="true" />个人部署可只使用账号密码登录，无需配置 SMS 服务。</p>
      </div>
    </section>
  </main>
</template>
