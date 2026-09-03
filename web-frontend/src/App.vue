<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, onUnmounted, provide, ref, watch, type Component } from "vue"

import WebSidebar, { type WorkspaceView } from "./components/WebSidebar.vue"
import LoginPanel from "./components/LoginPanel.vue"
import WebTopbar from "./components/WebTopbar.vue"
import LoadingSpinner from "./components/LoadingSpinner.vue"
import AsyncViewError from "./components/AsyncViewError.vue"
import { requestApi, SESSION_EXPIRED_EVENT } from "./lib/api"
import { CAPABILITIES_KEY, createCapabilityContext } from "./lib/capabilities"
import { NAVIGATION_GUARD_KEY, createNavigationGuardContext } from "./lib/navigation-guard"
import { clearSession, readSession, type Session } from "./lib/session"
import { buildWorkspaceUrl, getWorkspacePageTitle, parseWorkspaceRoute, type WorkspaceRoute } from "./lib/workspace-route"

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
const initialRoute: WorkspaceRoute = typeof window === "undefined"
  ? { view: "overview", draftId: null }
  : parseWorkspaceRoute({ search: window.location.search })
const activeView = ref<WorkspaceView>(initialRoute.view)
const pendingNavigation = ref<WorkspaceView | null>(null)
const pendingDraftId = ref<string | null>(null)
const editingDraftId = ref<string | null>(initialRoute.draftId)
const dark = ref(false)
const logoutLoading = ref(false)
const sessionExpired = ref(false)
let themeSwitchTimer: number | undefined
let themeInitialized = false
let suppressRouteSync = false
const activeComponent = computed(() => viewComponents[activeView.value])

function currentRoute(): WorkspaceRoute {
  return { view: activeView.value, draftId: editingDraftId.value }
}

function applyRoute(route: WorkspaceRoute): void {
  suppressRouteSync = true
  activeView.value = route.view
  editingDraftId.value = route.draftId
  suppressRouteSync = false
  if (typeof document !== "undefined") document.title = getWorkspacePageTitle(route)
}

function updateRoute(route: WorkspaceRoute, replace = false): void {
  if (typeof window === "undefined") return
  const nextUrl = buildWorkspaceUrl(route, window.location.href)
  if (replace) window.history.replaceState({}, "", nextUrl)
  else window.history.pushState({}, "", nextUrl)
  if (typeof document !== "undefined") document.title = getWorkspacePageTitle(route)
}

function navigateTo(view: WorkspaceView): void {
  if (view === activeView.value && !editingDraftId.value) return
  if (!navigationContext.canNavigate()) {
    pendingNavigation.value = view
    pendingDraftId.value = null
    return
  }
  pendingNavigation.value = null
  pendingDraftId.value = null
  const route: WorkspaceRoute = { view, draftId: null }
  applyRoute(route)
  updateRoute(route)
}

function resumePendingNavigation(): void {
  const target = pendingNavigation.value
  const draftId = pendingDraftId.value
  pendingNavigation.value = null
  pendingDraftId.value = null
  if (!target) return
  if (draftId) {
    const route: WorkspaceRoute = { view: "resume", draftId }
    applyRoute(route)
    updateRoute(route)
    return
  }
  navigateTo(target)
}

function handlePopState(): void {
  const route = parseWorkspaceRoute({ search: window.location.search })
  if (!navigationContext.canNavigate()) {
    pendingNavigation.value = route.view
    pendingDraftId.value = route.draftId
    updateRoute(currentRoute(), true)
    return
  }
  pendingNavigation.value = null
  pendingDraftId.value = null
  applyRoute(route)
}

function handleSessionExpired(): void {
  sessionExpired.value = true
  session.value = null
}

watch(session, (value) => {
  if (value) sessionExpired.value = false
})

watch(editingDraftId, (draftId, previousDraftId) => {
  if (suppressRouteSync || draftId === previousDraftId) return
  if (draftId) activeView.value = "resume"
  updateRoute({ view: draftId ? "resume" : activeView.value, draftId })
})

onMounted(() => {
  applyRoute(currentRoute())
  window.addEventListener("popstate", handlePopState)
  window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired)
})

onUnmounted(() => {
  window.removeEventListener("popstate", handlePopState)
  window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired)
  if (themeSwitchTimer !== undefined) window.clearTimeout(themeSwitchTimer)
})

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
  <LoginPanel v-if="!session" :session-notice="sessionExpired ? '登录已过期，请重新登录后继续。' : undefined" @authenticated="session = $event" />
  <div v-else class="web-shell">
    <WebSidebar :active-view="activeView" @navigate="navigateTo" />
    <main class="web-workspace">
      <WebTopbar :user="session.user" :dark="dark" :logout-loading="logoutLoading" @logout="logout" @toggle-theme="dark = !dark" />
      <section class="workspace-stage" :aria-labelledby="editingDraftId ? 'resume-editor-title' : `${activeView}-title`">
        <Transition name="view-swap" mode="out-in">
          <template v-if="editingDraftId">
            <ResumeEditorView
              v-if="editingDraftId"
              :key="`resume-editor-${editingDraftId}`"
              class="view-transition-shell"
              :draft-id="editingDraftId"
              @cancel="editingDraftId = null"
              @saved="editingDraftId = null"
            />
          </template>
          <KeepAlive v-else>
            <component :is="activeComponent" :key="activeView" class="view-transition-shell" @navigate="navigateTo" @navigation-ready="resumePendingNavigation" @open-draft="editingDraftId = $event" />
          </KeepAlive>
        </Transition>
      </section>
    </main>
  </div>
</template>
