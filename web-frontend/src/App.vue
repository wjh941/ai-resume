<script setup lang="ts">
import { computed, ref, watch } from "vue"

import WebSidebar, { type WorkspaceView } from "./components/WebSidebar.vue"
import LoginPanel from "./components/LoginPanel.vue"
import WebTopbar from "./components/WebTopbar.vue"
import { requestApi } from "./lib/api"
import { clearSession, readSession, type Session } from "./lib/session"

const session = ref<Session | null>(readSession())
const activeView = ref<WorkspaceView>("overview")
const dark = ref(false)
const pageTitle = computed(() => ({
  overview: "工作概览",
  resume: "简历中心",
  career: "职业规划",
  jobs: "岗位机会",
  applications: "投递管理",
  insights: "年度洞察",
  account: "账户设置",
}[activeView.value]))

watch(dark, (value) => {
  document.documentElement.dataset.theme = value ? "dark" : "light"
}, { immediate: true })

async function logout() {
  try {
    await requestApi("/api/auth/logout", { method: "POST" })
  } catch {
    // Local session cleanup is still correct when a token has already expired.
  } finally {
    clearSession()
    session.value = null
  }
}
</script>

<template>
  <LoginPanel v-if="!session" @authenticated="session = $event" />
  <div v-else class="web-shell">
    <WebSidebar :active-view="activeView" @navigate="activeView = $event" />
    <main class="web-workspace">
      <WebTopbar :user="session.user" :dark="dark" @logout="logout" @toggle-theme="dark = !dark" />
      <section class="workspace-stage" :aria-labelledby="`${activeView}-title`">
        <div class="workspace-heading">
          <h1 :id="`${activeView}-title`">{{ pageTitle }}</h1>
          <p>正在加载与你的求职计划相关的内容。</p>
        </div>
        <div class="workspace-loading" role="status">
          <span class="loading-bar" aria-hidden="true" />
          <p>工作台模块正在准备中</p>
        </div>
      </section>
    </main>
  </div>
</template>
