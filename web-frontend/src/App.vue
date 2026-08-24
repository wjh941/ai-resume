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
import ResumeEditorView from "./views/ResumeEditorView.vue"

const session = ref<Session | null>(readSession())
const activeView = ref<WorkspaceView>("overview")
const editingDraftId = ref<string | null>(null)
const dark = ref(false)
const logoutLoading = ref(false)
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
  logoutLoading.value = true
  try {
    await requestApi("/api/auth/logout", { method: "POST" })
  } catch {
    // Local session cleanup is still correct when a token has already expired.
  } finally {
    clearSession()
    session.value = null
    logoutLoading.value = false
  }
}
</script>

<template>
  <LoginPanel v-if="!session" @authenticated="session = $event" />
  <div v-else class="web-shell">
    <WebSidebar :active-view="activeView" @navigate="activeView = $event" />
    <main class="web-workspace">
      <WebTopbar :user="session.user" :dark="dark" :logout-loading="logoutLoading" @logout="logout" @toggle-theme="dark = !dark" />
      <section class="workspace-stage" :aria-labelledby="editingDraftId ? 'resume-editor-title' : `${activeView}-title`">
        <Transition name="view-swap" mode="out-in">
          <div :key="editingDraftId ? `resume-editor-${editingDraftId}` : activeView" class="view-transition-shell">
            <ResumeEditorView
              v-if="editingDraftId"
              :draft-id="editingDraftId"
              @cancel="editingDraftId = null"
              @saved="editingDraftId = null"
            />
            <component v-else :is="activeComponent" @navigate="activeView = $event" @open-draft="editingDraftId = $event" />
          </div>
        </Transition>
      </section>
    </main>
  </div>
</template>
