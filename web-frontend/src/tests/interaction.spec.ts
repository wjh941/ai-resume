import { describe, expect, it } from "vitest"
import { existsSync, readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"

import { useAsyncAction } from "../composables/useAsyncAction"

describe("useAsyncAction", () => {
  it("provides one shared capability context and refreshes it without blocking App rendering", () => {
    const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
    expect(app).toContain("createCapabilityContext()")
    expect(app).toContain("CAPABILITIES_KEY")
    expect(app).toContain("provide(CAPABILITIES_KEY, context)")
    expect(app).toContain("void context.refresh()")
    expect(app).toContain('<LoginPanel v-if="!session"')
  })

  it("injects the shared capability context across capability-aware consumers", () => {
    const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
    const login = readFileSync(new URL("../components/LoginPanel.vue", import.meta.url), "utf8")
    const membership = readFileSync(new URL("../views/MembershipView.vue", import.meta.url), "utf8")
    const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
    const insights = readFileSync(new URL("../views/InsightsView.vue", import.meta.url), "utf8")

    for (const source of [login, membership, jobs, insights]) {
      expect(source).toContain("inject(CAPABILITIES_KEY")
      expect(source).toContain("context.capabilities")
    }
    expect(app).toContain("provide(CAPABILITIES_KEY, context)")
  })

  it("keeps SMS visible but gates its request when the capability is disabled", () => {
    const login = readFileSync(new URL("../components/LoginPanel.vue", import.meta.url), "utf8")
    expect(login).toContain("isCapabilityEnabled")
    expect(login).toContain("smsLogin")
    expect(login).toContain("send-code")
    expect(login).toContain(":disabled=\"!smsLoginEnabled")
    expect(login).toContain("smsLoginNotice")
    expect(login).toContain("if (!isCapabilityEnabled")
  })

  it("keeps password login as the fallback while capabilities are pending or unavailable", () => {
    const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
    const login = readFileSync(new URL("../components/LoginPanel.vue", import.meta.url), "utf8")
    expect(app).toContain("createCapabilityContext()")
    expect(app).toContain("void context.refresh()")
    expect(login).toContain('ref<"password" | "phone">("password")')
    expect(login).toContain("mode === 'password'")
    expect(login).toContain("loginWithPassword")
  })

  it("renders one primary focus, progress states, and recoverable continuation actions", () => {
    const overview = readFileSync(new URL("../views/OverviewView.vue", import.meta.url), "utf8")
    expect(overview).toContain("overview-focus")
    expect(overview).toContain("focus-action")
    expect(overview).toContain("focusOptions")
    expect(overview).toContain("换一件")
    expect(overview).toContain('v-if="overview.focusOptions.length > 1"')
    expect(overview).toContain("focusStatus.value =")
    expect(overview).toContain('emit("navigate", activeFocus.value!.target)')
    expect(overview).toContain('v-else-if="overview.hasWorkspaceData"')
    expect(overview.match(/class="focus-due"/g) ?? []).toHaveLength(1)
    expect(overview).toContain("progress-list")
    expect(overview).toContain("continue-list")
    expect(overview).toContain("鎹竴浠?")
    expect(overview).toContain('aria-live="polite"')
  })

  it("routes continuation resume items to the existing draft editor event", () => {
    const overview = readFileSync(new URL("../views/OverviewView.vue", import.meta.url), "utf8")

    expect(overview).toContain("function openContinuation(item: ContinuationItem)")
    expect(overview).toContain('if (item.kind === "resume" && item.id)')
    expect(overview).toContain('emit("open-draft", item.id)')
    expect(overview).toContain('emit("navigate", item.target)')
    expect(overview).toContain("focusStatus.value =")
    expect(overview).toContain("void nextTick(() => {")
  })

  it("keeps continuation buttons accessible and distinguishes resume editing", () => {
    const overview = readFileSync(new URL("../views/OverviewView.vue", import.meta.url), "utf8")

    expect(overview).toContain('item.kind === "resume" ? "继续编辑" : "继续"')
    expect(overview).toContain(":aria-label=")
    expect(overview).toContain("openContinuation(item)")
  })

  it("falls back to resume navigation when a continuation has no draft id", () => {
    const overview = readFileSync(new URL("../views/OverviewView.vue", import.meta.url), "utf8")

    expect(overview).toContain('if (item.kind === "resume" && item.id)')
    expect(overview).toContain('emit("open-draft", item.id)')
    expect(overview).toContain('if (item.kind === "resume")')
    expect(overview).toContain('emit("navigate", "resume")')
    expect(overview).toMatch(/if \(item\.kind === "resume" && item\.id\) \{[\s\S]*emit\("open-draft", item\.id\)[\s\S]*return[\s\S]*if \(item\.kind === "resume"\) \{[\s\S]*emit\("navigate", "resume"\)[\s\S]*return[\s\S]*emit\("navigate", item\.target\)/)
    expect(overview).toContain("void nextTick(() => {")
  })

  it("keeps the future capability shell presentation-only", () => {
    const source = readFileSync(new URL("../components/FutureCapabilityShell.vue", import.meta.url), "utf8")
    expect(source).not.toContain("requestApi")
    expect(source).not.toContain("fetch(")
  })

  it("clears pending after a successful operation", async () => {
    const action = useAsyncAction()
    const result = await action.run(async () => "saved")

    expect(result).toBe("saved")
    expect(action.pending.value).toBe(false)
  })

  it("clears pending and rethrows after a failed operation", async () => {
    const action = useAsyncAction()
    const failure = Promise.resolve().then(() => action.run(async () => { throw new Error("network") }))

    await expect(failure).rejects.toThrow("network")
    expect(action.pending.value).toBe(false)
  })

  it("ignores a duplicate operation while pending", async () => {
    const action = useAsyncAction()
    let resolve!: (value: string) => void
    const first = action.run(() => new Promise<string>((done) => { resolve = done }))
    const second = await action.run(async () => "duplicate")

    expect(second).toBeUndefined()
    resolve("first")
    await expect(first).resolves.toBe("first")
  })

  it("locks career task controls while a task update is pending", () => {
    const source = readFileSync(new URL("../views/CareerView.vue", import.meta.url), "utf8")
    expect(source).toContain("if (pendingTaskId.value) return")
    expect(source).toContain(':loading="pendingTaskId === task.id" :disabled="Boolean(pendingTaskId)"')
  })

  it("uses the career task adapter and camelCase due dates", () => {
    const source = readFileSync(new URL("../views/CareerView.vue", import.meta.url), "utf8")
    expect(source).toContain('listCareerTasks, type CareerTaskRecord')
    expect(source).toContain("tasks.value = await listCareerTasks(planId)")
    expect(source).toContain("task.dueDate")
    expect(source).toContain("{{ task.dueDate }}")
  })

  it("locks application follow-up controls while one request is pending", () => {
    const source = readFileSync(new URL("../views/ApplicationsView.vue", import.meta.url), "utf8")
    expect(source).toContain(':loading="pendingKey === `timeline-load:${item.id}`" :disabled="Boolean(pendingKey)"')
    expect(source).toContain(':loading="pendingKey === `timeline-add:${item.id}`" :disabled="Boolean(pendingKey)"')
    expect(source).toContain(':loading="pendingKey === `reminder:${item.id}`" :disabled="Boolean(pendingKey)"')
  })

  it("guards account actions and mode switches while requests are pending", () => {
    const account = readFileSync(new URL("../views/AccountView.vue", import.meta.url), "utf8")
    const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
    const insights = readFileSync(new URL("../views/InsightsView.vue", import.meta.url), "utf8")
    const assessment = readFileSync(new URL("../views/AssessmentView.vue", import.meta.url), "utf8")
    expect(account).toContain("if (pendingAction.value) return")
    expect(account).toContain(':disabled="Boolean(pendingAction)"')
    expect(jobs).toContain(':disabled="loading"')
    expect(insights).toContain(':disabled="loading"')
    expect(assessment).toContain(':disabled="saving"')
  })

  it("uses one semantic error feedback contract across business views", () => {
    const notice = readFileSync(new URL("../components/ErrorNotice.vue", import.meta.url), "utf8")
    const overview = readFileSync(new URL("../views/OverviewView.vue", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../views/ApplicationsView.vue", import.meta.url), "utf8")
    expect(notice).toContain('role="alert"')
    expect(notice).toContain("notice-error")
    expect(overview).toContain("<ErrorNotice")
    expect(applications).toContain("<ErrorNotice")
  })

  it("keeps theme switching and responsive bounds centralized", () => {
    const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")
    expect(app).toContain("theme-switching")
    expect(styles).toContain("--theme-transition")
    expect(styles).toContain("html.theme-switching")
    expect(styles).toContain("@media (max-width: 380px)")
    expect(styles).toContain("@media (min-width: 1600px)")
  })

  it("keeps the dashboard action layout bounded across viewport sizes", () => {
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")
    expect(styles).toContain(".overview-focus")
    expect(styles).toContain(".progress-list")
    expect(styles).toContain(".continue-list")
    expect(styles).toMatch(/@media \(max-width: 840px\)/)
    expect(styles).toContain("min-width: 0")
  })

  it("assigns dashboard progress states and stable touch targets", () => {
    const overview = readFileSync(new URL("../views/OverviewView.vue", import.meta.url), "utf8")
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")
    expect(overview).toContain(':data-state="item.state"')
    expect(styles).toContain('.progress-row[data-state="completed"]')
    expect(styles).toContain('.progress-row[data-state="in-progress"]')
    expect(styles).toContain('.progress-row[data-state="not-started"]')
    expect(styles).toContain(".focus-controls .text-action")
    expect(styles).toContain(".view-layout > .notice-error .notice-action")
    expect(styles).toMatch(/\.focus-controls \.text-action[^}]*min-height: 44px/s)
    expect(styles).toMatch(/\.view-layout > \.notice-error \.notice-action[^}]*min-height: 44px/s)
  })

  it("keeps the dashboard refresh control touch-safe and motion-safe", () => {
    const overview = readFileSync(new URL("../views/OverviewView.vue", import.meta.url), "utf8")
    expect(overview).toMatch(/\.overview-hero \.text-action\s*\{[^}]*min-height:\s*44px[^}]*min-width:\s*0[^}]*max-width:\s*100%[^}]*overflow-wrap:\s*anywhere/s)
    expect(overview).toMatch(/@media \(prefers-reduced-motion:\s*reduce\)[\s\S]*\.overview-hero \.text-action[^}]*transform:\s*none\s*!important/s)
  })

  it("contains off-screen Web records and disables theme motion when requested", () => {
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")
    expect(styles).toContain("content-visibility: auto")
    expect(styles).toContain("contain-intrinsic-size")
    expect(styles).toContain("html.theme-switching .web-shell *")
    expect(styles).toContain(".notice-error::before")
    expect(styles).toContain("prefers-reduced-motion: reduce")
  })

  it("guards rapid Web actions and exposes accessible context", () => {
    const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
    const login = readFileSync(new URL("../components/LoginPanel.vue", import.meta.url), "utf8")
    const topbar = readFileSync(new URL("../components/WebTopbar.vue", import.meta.url), "utf8")
    const career = readFileSync(new URL("../views/CareerView.vue", import.meta.url), "utf8")
    const evidence = readFileSync(new URL("../views/EvidenceView.vue", import.meta.url), "utf8")
    const insights = readFileSync(new URL("../views/InsightsView.vue", import.meta.url), "utf8")
    const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../views/ApplicationsView.vue", import.meta.url), "utf8")
    const resume = readFileSync(new URL("../views/ResumeView.vue", import.meta.url), "utf8")

    expect(app).toContain("if (logoutLoading.value) return")
    expect(login).toContain("if (loading.value || sending.value) return")
    expect(career).toContain("if (saving.value) return")
    expect(evidence).toContain("if (readinessLoading.value) return")
    expect(insights).toContain("if (loading.value) return")
    expect(jobs).toContain("if (loading.value) return")
    expect(jobs).toContain("if (!result.value || saving.value) return")
    expect(login).toContain("aria-describedby")
    expect(login).toContain("aria-invalid")
    expect(topbar).toContain(':aria-pressed="dark"')
    expect(applications).toContain(":aria-label=")
    expect(resume).toContain(":aria-label=")
  })

  it("organizes existing destinations into task-oriented navigation groups", () => {
    const sidebar = readFileSync(new URL("../components/WebSidebar.vue", import.meta.url), "utf8")
    expect(sidebar).toContain("navigationGroups")
    expect(sidebar).toContain("准备资料")
    expect(sidebar).toContain("职业决策")
    expect(sidebar).toContain("求职执行")
    expect(sidebar).toContain("复盘与账户")
    expect(sidebar).toContain("navigation-group")
    expect(sidebar).toContain("item.key")
  })

  it("turns a missing career profile into an actionable comparison state", () => {
    const comparison = readFileSync(new URL("../views/ComparisonView.vue", import.meta.url), "utf8")
    expect(comparison).toContain("profileMissing")
    expect(comparison).toContain("isCareerProfileMissingError(caught)")
    expect(comparison).toContain("职业规划")
    expect(comparison).toContain("profile-missing")
  })

  it("gives the primary job query a visible visual anchor", () => {
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")
    expect(styles).toMatch(/\.role-query \{[^}]*border: 1px solid color-mix\(in srgb, var\(--coral\)/s)
    expect(styles).toMatch(/\.job-result \{[^}]*box-shadow: inset 0 2px 0 var\(--primary\), var\(--shadow-panel\)/s)
    expect(styles).toContain("--accent-tint:")
  })

  it("renders complete, actionable job intelligence instead of a truncated summary", () => {
    const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
    expect(jobs).toContain("hard_requirements")
    expect(jobs).toContain("required_skills")
    expect(jobs).toContain("bonus_skills")
    expect(jobs).toContain("career_route")
    expect(jobs).toContain("interviewChecks")
    expect(jobs).toContain("report?.evidence")
    expect(jobs).toContain("report?.upgrade_notice")
    expect(jobs).toContain("核验")
    expect(jobs).not.toContain("responsibilities?.slice(0, 4)")
    expect(jobs).not.toContain("slice(0, 8)")
  })

  it("provides accessible long-text expansion in read-only business content", () => {
    const componentUrl = new URL("../components/ExpandableText.vue", import.meta.url)
    expect(existsSync(fileURLToPath(componentUrl))).toBe(true)

    const component = readFileSync(componentUrl, "utf8")
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../views/ApplicationsView.vue", import.meta.url), "utf8")
    const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
    const resume = readFileSync(new URL("../views/ResumeView.vue", import.meta.url), "utf8")
    const evidence = readFileSync(new URL("../views/EvidenceView.vue", import.meta.url), "utf8")

    expect(component).toContain('aria-expanded')
    expect(component).toContain('aria-controls')
    expect(styles).toContain('.expandable-copy.is-collapsed')
    expect(styles).toContain('-webkit-line-clamp')
    expect(applications).toContain('<ExpandableText')
    expect(jobs).toContain('<ExpandableText')
    expect(resume).toContain('<ExpandableText')
    expect(evidence).toContain('<ExpandableText')
  })

  it("wires local checkpoint and inline validation into the resume editor", () => {
    const editor = readFileSync(new URL("../views/ResumeEditorView.vue", import.meta.url), "utf8")
    const orchestration = readFileSync(new URL("../lib/resume-editor-orchestration.ts", import.meta.url), "utf8")
    expect(editor).toContain("createResumeEditorOrchestration")
    expect(editor).toContain("readDraftCheckpoint")
    expect(editor).toContain("writeDraftCheckpoint")
    expect(orchestration).toContain("createDebouncedTask")
    expect(editor).toContain("validateDraft")
    expect(editor).toContain("local-save-status")
    expect(orchestration).toContain("localCheckpoint.flush()")
    expect(editor).toContain("clearDraftCheckpoint")
    expect(orchestration).toContain("checkpointPaused")
    expect(editor).toContain('aria-live="polite"')
  })

  it("wires scoped shortcuts and inline business-form feedback", () => {
    const editor = readFileSync(new URL("../views/ResumeEditorView.vue", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../views/ApplicationsView.vue", import.meta.url), "utf8")
    const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
    const assessment = readFileSync(new URL("../views/AssessmentView.vue", import.meta.url), "utf8")
    const questionCard = readFileSync(new URL("../components/AssessmentQuestionCard.vue", import.meta.url), "utf8")

    expect(editor).toContain("resolveWorkspaceShortcut")
    expect(editor).toContain('window.addEventListener("keydown"')
    expect(editor).toContain('window.removeEventListener("keydown"')
    expect(applications).toContain("resolveWorkspaceShortcut")
    expect(applications).toContain("resolveApplicationsCloseAction")
    expect(jobs).toContain('const roleFieldError = ref("")')
    expect(jobs).toContain('id="jobs-role-error"')
    expect(assessment).toContain(":invalid=\"validationActive && !Number.isInteger(answers[question.key])\"")
    expect(assessment).toContain("resolveAssessmentSubmitAction")
    expect(questionCard).toContain(':aria-invalid="invalid || undefined"')
  })

  it("routes invalid resume saves and visible cancel controls through accessible shared handlers", () => {
    const editor = readFileSync(new URL("../views/ResumeEditorView.vue", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../views/ApplicationsView.vue", import.meta.url), "utf8")
    const normalizedEditor = editor.replace(/\s+/g, " ")

    expect(editor).toContain("focusFirstInvalidResumeField")
    expect(editor).toContain("createResumeInvalidFeedback")
    expect.soft(normalizedEditor).toMatch(/async function save\(\): Promise<void> \{ resetInvalidSummary\(\) const result = await saveEditor\(\)/)
    expect.soft(normalizedEditor).toMatch(/if \(result === "invalid"\) \{ activateInvalidSummary\(fieldErrors\.value\) await nextTick\(\) focusFirstInvalidResumeField\(fieldErrors\.value\) \}/)
    expect.soft(normalizedEditor).toMatch(/watch\(fieldErrors, \(currentErrors\) => \{ syncInvalidSummary\(currentErrors\) \}, \{ deep: true \}\)/)
    expect(editor).toContain('role="alert"')
    expect(editor).toContain('@click="cancel"')
    expect(editor).toContain('else if (action === "back") cancel()')
    expect(editor).toContain(':disabled="loading || saving"')
    expect(applications).toContain('@click="cancelEditing"')
    expect(applications).toContain('if (action === "reset") cancelEditing()')
    expect(applications).toContain(':disabled="loading || Boolean(pendingKey)"')
  })

  it("protects dirty resume edits before leaving the editor", () => {
    const editor = readFileSync(new URL("../views/ResumeEditorView.vue", import.meta.url), "utf8")
    const normalizedEditor = editor.replace(/\s+/g, " ")

    expect(editor).toContain("isDirty")
    expect(editor).toContain("localSaveState")
    expect(editor).toContain("clearDraftCheckpoint")
    expect(editor).toContain('"正在保存到本机"')
    expect(editor).toContain('"已保存到本机，尚未同步"')
    expect(editor).toContain('"已同步到云端"')
    expect(editor).toContain('"本机自动保存失败，请手动保存"')
    expect(editor).toContain("showLeaveConfirmation")
    expect(editor).toContain("discardLocalCheckpoint")
    expect(editor).toContain("继续编辑")
    expect(editor).toContain("放弃并返回")
    expect(editor).toMatch(/discardLocalCheckpoint\(props\.draftId\)[\s\S]*emit\("cancel"\)/)
    expect(editor).toContain('window.addEventListener("beforeunload"')
    expect(editor).toContain('window.removeEventListener("beforeunload"')
    expect(normalizedEditor).toMatch(/event\.preventDefault\(\) event\.returnValue = ""/)
  })

  it("observes a late-mounted progressive list sentinel with a manual fallback", () => {
    const sentinel = readFileSync(new URL("../components/ProgressiveListSentinel.vue", import.meta.url), "utf8")

    expect(sentinel).toContain("IntersectionObserver")
    expect(sentinel).toContain("watch(target")
    expect(sentinel).toContain("observer?.disconnect()")
    expect(sentinel).toContain('type="button"')
    expect(sentinel).toContain("emit('more')")
  })

  it("bounds large Web lists and stabilizes the wide application grid", () => {
    const resume = readFileSync(new URL("../views/ResumeView.vue", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../views/ApplicationsView.vue", import.meta.url), "utf8")
    const evidence = readFileSync(new URL("../views/EvidenceView.vue", import.meta.url), "utf8")
    const membership = readFileSync(new URL("../views/MembershipView.vue", import.meta.url), "utf8")
    const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")

    for (const source of [resume, applications, evidence, membership]) {
      expect(source).toContain("useIncrementalList")
      expect(source).toContain("ProgressiveListSentinel")
    }
    expect(styles).toContain("overflow-x: auto")
    expect(styles).toContain(".record-list, .task-list, .application-table, .evidence-list, .order-list")
    expect(styles).toContain("grid-template-columns: 40px minmax(220px, 1fr) 128px 170px minmax(250px, auto)")
    expect(resume).toContain("本机编辑内容会自动保留，手动保存后同步到服务端。")
    expect(applications).toContain("可直接使用上方表单新增第一条记录。")
    expect(jobs).toContain("输入具体岗位名称后开始整理能力要求。")
  })

  it("loads workspace views on demand with the shared loading state", () => {
    const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
    expect(app).toContain("defineAsyncComponent")
    expect(app).toContain('import LoadingSpinner from "./components/LoadingSpinner.vue"')
    expect(app).toContain("loadingComponent: LoadingSpinner")
    for (const view of [
      "OverviewView",
      "ResumeView",
      "CareerView",
      "JobsView",
      "ApplicationsView",
      "EvidenceView",
      "MembershipView",
      "AssessmentView",
      "ComparisonView",
      "InsightsView",
      "AccountView",
      "ResumeEditorView",
    ]) {
      expect(app).toContain(`import(\"./views/${view}.vue\")`)
    }
    expect(app).toContain('mode="out-in"')
    expect(app).toContain('@navigate="activeView = $event"')
  })

  it("forwards overview draft openings to the existing editor state", () => {
    const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")

    expect(app).toContain('@open-draft="editingDraftId = $event"')
    expect(app).toContain('v-if="editingDraftId"')
    expect(app).toContain(':draft-id="editingDraftId"')
  })

  it("shows a bounded async-view load failure instead of a blank stage", () => {
    const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
    const errorView = readFileSync(new URL("../components/AsyncViewError.vue", import.meta.url), "utf8")
    expect(app).toContain('import AsyncViewError from "./components/AsyncViewError.vue"')
    expect(app).toContain("errorComponent: AsyncViewError")
    expect(app).toContain("onError(error, retry, fail, attempts)")
    expect(app).toContain("if (attempts <= 2) retry()")
    expect(app).toContain("fail(error)")
    expect(errorView).toContain("<ErrorNotice")
    expect(errorView).toContain('message="页面加载失败，请刷新后重试"')
    expect(errorView).toContain("compact")
  })

  it("uses restrained hover elevation for high-value workspace surfaces", () => {
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")
    expect(styles).toContain("--shadow-hover:")
    expect(styles).toContain("@media (hover: hover)")
    expect(styles).toContain(".metric-block:hover")
    expect(styles).toContain(".comparison-card:hover")
    expect(styles).toContain(".membership-package:hover")
    expect(styles).toContain(".assessment-question:not(.is-invalid):hover")
    expect(styles).toContain("transform: translateY(-2px)")
  })

  it("assigns distinct surface roles to tools and records", () => {
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")
    expect(styles).toContain("--surface-soft:")
    expect(styles).toContain("--surface-inset:")
    expect(styles).toContain("--shadow-panel:")
    expect(styles).toMatch(/\.workbench-form \{[^}]*background: var\(--surface-soft\)[^}]*box-shadow: var\(--shadow-panel\)/s)
    expect(styles).toMatch(/\.record-surface \{[^}]*background: var\(--surface-inset\)/s)
    expect(styles).toContain(":root[data-theme=\"dark\"] .record-surface")
  })

  it("ships the physical capsule interaction contract", () => {
    const capsule = readFileSync(new URL("../components/CapsuleMultiSelect.vue", import.meta.url), "utf8")
    const picker = readFileSync(new URL("../components/ComparisonRolePicker.vue", import.meta.url), "utf8")
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")

    expect(capsule).toContain("pointerdown")
    expect(capsule).toContain("AsyncButton")
    expect(capsule).toContain("ripple-x")
    expect(capsule).toContain("skeletonCount")
    expect(capsule).toContain("requestAnimationFrame")
    expect(styles).toContain("rotateY")
    expect(capsule).toContain("capsule-particle")
    expect(styles).toContain(".capsule-tag:active:not(:disabled)")
    expect(styles).toContain("transform: scale(0.92)")
    expect(styles).toContain("cubic-bezier(0.34, 1.56, 0.64, 1)")
    expect(styles).toContain("capsule-tag-check-draw")
    expect(styles).toContain("capsule-elastic")
    expect(styles).toContain("capsule-progress-fill")
    expect(styles).toContain("capsule-tag-skeleton")
    expect(styles).toContain("capsule-particle")
  })

  it("ships the physical sidebar interaction contract", () => {
    const sidebar = readFileSync(new URL("../components/WebSidebar.vue", import.meta.url), "utf8")
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")

    expect(sidebar).toContain("sidebar-drawer-backdrop")
    expect(sidebar).toContain("Escape")
    expect(sidebar).toContain("sidebar-toggle-icon")
    expect(sidebar).toContain("<path")
    expect(sidebar).toContain("toggleGroup")
    expect(sidebar).toContain("liquid-slider")
    expect(styles).toContain("sidebar-drawer-in")
    expect(styles).toContain("sidebar-drawer-out")
    expect(styles).toContain("group-swipe")
    expect(styles).toContain("liquid-slider-fill")
  })

  it("defines visual trust-state contracts for analysis modes", () => {
    const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")

    expect(styles).toContain(".mode-notice")
    expect(styles).toContain(".mode-notice.is-demo")
    expect(styles).toContain(".mode-notice.is-unavailable")
    expect(styles).toContain(".mode-switch button.is-unavailable")
    expect(styles).toContain('[aria-disabled="true"]')
    expect(styles).toMatch(/\.mode-switch button\.is-unavailable \{[^}]*opacity:\s*[^;]+;[^}]*cursor:\s*not-allowed/s)
    expect(styles).toMatch(/\.mode-switch button\.is-selected\.is-unavailable \{[^}]*background:[^}]*!important/s)
    expect(styles).toMatch(/\.mode-notice\.is-demo \{[^}]*var\(--primary[^}]*var\(--primary-tint/s)
    expect(styles).not.toMatch(/\.mode-notice\.is-demo \{[^}]*var\(--(?:success|accent|coral)/s)
    expect(styles).toMatch(/\.mode-recovery-actions \{[^}]*display:\s*flex;[^}]*flex-wrap:\s*wrap/s)
    expect(styles).toContain("@media (max-width: 480px)")
    expect(styles).toContain(".mode-recovery-actions .notice-action")
  })
})
