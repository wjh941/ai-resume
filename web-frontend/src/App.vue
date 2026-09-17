<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, onUnmounted, provide, ref, watch, type Component } from "vue"

import WebSidebar, { type WorkspaceView } from "./components/WebSidebar.vue"
import LoginPanel from "./components/LoginPanel.vue"
import WebTopbar from "./components/WebTopbar.vue"
import LoadingSpinner from "./components/LoadingSpinner.vue"
import AsyncViewError from "./components/AsyncViewError.vue"
import { requestApi, SESSION_EXPIRED_EVENT } from "./lib/api"
import { createBackendWakeMonitor } from "./lib/backend-wake"
import { CAPABILITIES_KEY, createCapabilityContext } from "./lib/capabilities"
import { NAVIGATION_GUARD_KEY, createNavigationGuardContext } from "./lib/navigation-guard"
import { clearSession, readSession, type Session } from "./lib/session"
import { readStoredTheme, resolveInitialDarkTheme, storeTheme, watchSystemTheme } from "./lib/theme"
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
      else fail()
    },
  })
}

const viewLoaders: Record<WorkspaceView, () => Promise<{ default: Component }>> = {
  overview: () => import("./views/OverviewView.vue"),
  resume: () => import("./views/ResumeView.vue"),
  career: () => import("./views/CareerView.vue"),
  jobs: () => import("./views/JobsView.vue"),
  applications: () => import("./views/ApplicationsView.vue"),
  evidence: () => import("./views/EvidenceView.vue"),
  membership: () => import("./views/MembershipView.vue"),
  assessment: () => import("./views/AssessmentView.vue"),
  comparison: () => import("./views/ComparisonView.vue"),
  insights: () => import("./views/InsightsView.vue"),
  account: () => import("./views/AccountView.vue"),
}
const viewComponents = Object.fromEntries(
  (Object.keys(viewLoaders) as WorkspaceView[]).map((view) => [view, asyncView(viewLoaders[view])]),
) as Record<WorkspaceView, Component>
const ResumeEditorView = asyncView(() => import("./views/ResumeEditorView.vue"))

// 指针悬停/键盘聚焦侧边栏时提前加载目标视图 chunk，点击时几乎零等待。
const warmedViews = new Set<WorkspaceView>()
function prefetchView(view: WorkspaceView): void {
  if (warmedViews.has(view)) return
  warmedViews.add(view)
  void viewLoaders[view]().catch(() => warmedViews.delete(view))
}

const session = ref<Session | null>(readSession())
const context = createCapabilityContext()
provide(CAPABILITIES_KEY, context)
void context.refresh()
// 免费托管冷启动：进站先探活 /health，失败时轮询并在界面提示“服务唤醒中”，
// 避免用户在冷启动窗口里看到一串超时报错。
const backendWake = createBackendWakeMonitor({
  requestFn: () => requestApi("/health", {}, { timeoutMs: 10_000 }).then(() => true),
})
const navigationContext = createNavigationGuardContext()
provide(NAVIGATION_GUARD_KEY, navigationContext)
const initialRoute: WorkspaceRoute = typeof window === "undefined"
  ? { view: "overview", draftId: null }
  : parseWorkspaceRoute({ search: window.location.search })
const activeView = ref<WorkspaceView>(initialRoute.view)
const pendingNavigation = ref<WorkspaceView | null>(null)
const pendingDraftId = ref<string | null>(null)
const editingDraftId = ref<string | null>(initialRoute.draftId)
const dark = ref(resolveInitialDarkTheme())
const logoutLoading = ref(false)
const sessionExpired = ref(false)
const accountDeletedNotice = ref("")
let themeSwitchTimer: number | undefined
let themeInitialized = false
let stopSystemThemeWatch: (() => void) | undefined
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

function handleAccountDeleted(): void {
  clearSession()
  accountDeletedNotice.value = "账户已删除，感谢你使用本工作区。"
  session.value = null
}

watch(session, (value) => {
  if (value) {
    sessionExpired.value = false
    accountDeletedNotice.value = ""
  }
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
  // 用户未显式选择主题时跟随系统切换；一旦手动切换即写入存储，不再跟随。
  stopSystemThemeWatch = watchSystemTheme((prefersDark) => {
    if (readStoredTheme()) return
    dark.value = prefersDark
  })
  void backendWake.probe()
})

onUnmounted(() => {
  window.removeEventListener("popstate", handlePopState)
  window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired)
  if (themeSwitchTimer !== undefined) window.clearTimeout(themeSwitchTimer)
  stopSystemThemeWatch?.()
})

watch(dark, (value) => {
  const root = document.documentElement
  root.dataset.theme = value ? "dark" : "light"
  if (!themeInitialized) {
    themeInitialized = true
    return
  }
  storeTheme(value ? "dark" : "light")
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
  <div v-if="backendWake.waking.value" class="backend-wake-banner" role="status" aria-live="polite">
    <LoadingSpinner class="wake-spinner" label="正在唤醒后端服务" />
    <span>后端服务正在唤醒（免费托管冷启动，预计 30-50 秒），已自动重试 {{ backendWake.attempts.value }} 次，稍候即可正常使用。</span>
  </div>
  <LoginPanel v-if="!session" :session-notice="sessionExpired ? '登录已过期，请重新登录后继续。' : accountDeletedNotice || undefined" @authenticated="session = $event" />
  <div v-else class="web-shell">
    <WebSidebar :active-view="activeView" @navigate="navigateTo" @prefetch="prefetchView" />
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
            <component :is="activeComponent" :key="activeView" class="view-transition-shell" @navigate="navigateTo" @deleted="handleAccountDeleted" @navigation-ready="resumePendingNavigation" @open-draft="editingDraftId = $event" />
          </KeepAlive>
        </Transition>
      </section>
    </main>
  </div>
</template>
