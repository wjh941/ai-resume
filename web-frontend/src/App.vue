<script setup lang="ts">
import { computed, defineAsyncComponent, provide, ref, watch, type Component } from "vue"

import WebSidebar, { type WorkspaceView } from "./components/WebSidebar.vue"
import LoginPanel from "./components/LoginPanel.vue"
import WebTopbar from "./components/WebTopbar.vue"
import LoadingSpinner from "./components/LoadingSpinner.vue"
import AsyncViewError from "./components/AsyncViewError.vue"
import { requestApi } from "./lib/api"
import { CAPABILITIES_KEY, createCapabilityContext } from "./lib/capabilities"
import { NAVIGATION_GUARD_KEY, createNavigationGuardContext } from "./lib/navigation-guard"
import { clearSession, readSession, type Session } from "./lib/session"

function asyncView(loader: () => Promise<{ default: Component }>): Component {
  return defineAsyncComponent({
    loader,
    loadingComponent: LoadingSpinner,
    errorComponent: AsyncViewError,
    delay: 120,
    suspensible: false,
    onError(error, retry, fail, attempts) {
      if (attempts <= 2) retry()
      else fail(error)
    },
  })
}

const viewComponents: Record<WorkspaceView, Component> = {
  overview: asyncView(() => import("./views/OverviewView.vue")),
  resume: asyncView(() => import("./views/ResumeView.vue")),
  career: asyncView(() => import("./views/CareerView.vue")),
  jobs: asyncView(() => import("./views/JobsView.vue")),
  applications: asyncView(() => import("./views/ApplicationsView.vue")),
  evidence: asyncView(() => import("./views/EvidenceView.vue")),
  membership: asyncView(() => import("./views/MembershipView.vue")),
  assessment: asyncView(() => import("./views/AssessmentView.vue")),
  comparison: asyncView(() => import("./views/ComparisonView.vue")),
  insights: asyncView(() => import("./views/InsightsView.vue")),
  account: asyncView(() => import("./views/AccountView.vue")),
}
const ResumeEditorView = asyncView(() => import("./views/ResumeEditorView.vue"))

const session = ref<Session | null>(readSession())
const context = createCapabilityContext()
provide(CAPABILITIES_KEY, context)
void context.refresh()
const navigationContext = createNavigationGuardContext()
provide(NAVIGATION_GUARD_KEY, navigationContext)
const activeView = ref<WorkspaceView>("overview")
const pendingNavigation = ref<WorkspaceView | null>(null)
const editingDraftId = ref<string | null>(null)
const dark = ref(false)
const logoutLoading = ref(false)
let themeSwitchTimer: number | undefined
let themeInitialized = false
const activeComponent = computed(() => viewComponents[activeView.value])

function navigateTo(view: WorkspaceView): void {
  if (view === activeView.value) return
  if (!navigationContext.canNavigate()) {
    pendingNavigation.value = view
    return
  }
  pendingNavigation.value = null
  activeView.value = view
}

function resumePendingNavigation(): void {
  const target = pendingNavigation.value
  pendingNavigation.value = null
  if (target) navigateTo(target)
}

watch(dark, (value) => {
  const root = document.documentElement
  root.dataset.theme = value ? "dark" : "light"
  if (!themeInitialized) {
    themeInitialized = true
    return
  }
  root.classList.add("theme-switching")
  if (themeSwitchTimer !== undefined) window.clearTimeout(themeSwitchTimer)
  themeSwitchTimer = window.setTimeout(() => {
    root.classList.remove("theme-switching")
    themeSwitchTimer = undefined
  }, 220)
}, { immediate: true })

async function logout() {
  if (logoutLoading.value) return
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
    <WebSidebar :active-view="activeView" @navigate="navigateTo" />
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
            <component v-else :is="activeComponent" @navigate="navigateTo" @navigation-ready="resumePendingNavigation" @open-draft="editingDraftId = $event" />
          </div>
        </Transition>
      </section>
    </main>
  </div>
</template>
