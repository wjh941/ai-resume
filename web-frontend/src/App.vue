<script setup lang="ts">
import { computed, ref, watch } from "vue"

import WebSidebar, { type WorkspaceView } from "./components/WebSidebar.vue"
import LoginPanel from "./components/LoginPanel.vue"
import WebTopbar from "./components/WebTopbar.vue"
import { requestApi } from "./lib/api"
import { clearSession, readSession, type Session } from "./lib/session"
import AccountView from "./views/AccountView.vue"
import ApplicationsView from "./views/ApplicationsView.vue"
import CareerView from "./views/CareerView.vue"
import InsightsView from "./views/InsightsView.vue"
import JobsView from "./views/JobsView.vue"
import OverviewView from "./views/OverviewView.vue"
import ResumeView from "./views/ResumeView.vue"

const session = ref<Session | null>(readSession())
const activeView = ref<WorkspaceView>("overview")
const dark = ref(false)
const activeComponent = computed(() => ({
  overview: OverviewView,
  resume: ResumeView,
  career: CareerView,
  jobs: JobsView,
  applications: ApplicationsView,
  insights: InsightsView,
  account: AccountView,
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
        <Transition name="view-swap" mode="out-in">
          <div :key="activeView" class="view-transition-shell">
            <component :is="activeComponent" @navigate="activeView = $event" />
          </div>
        </Transition>
      </section>
    </main>
  </div>
</template>
