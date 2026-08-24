import { describe, expect, it } from "vitest"
import { existsSync, readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"

import { useAsyncAction } from "../composables/useAsyncAction"

describe("useAsyncAction", () => {
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

    expect(editor).toContain('result === "invalid"')
    expect(editor).toContain("focusFirstInvalidResumeField")
    expect(editor).toContain("resolveResumeInvalidSummary")
    expect(editor).toContain("invalidSummaryActive")
    expect(editor).toContain('role="alert"')
    expect(editor).toContain('@click="cancel"')
    expect(editor).toContain('else if (action === "back") cancel()')
    expect(editor).toContain(':disabled="loading || saving"')
    expect(applications).toContain('@click="cancelEditing"')
    expect(applications).toContain('if (action === "reset") cancelEditing()')
    expect(applications).toContain(':disabled="loading || Boolean(pendingKey)"')
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
    expect(styles).toContain("grid-template-columns: 40px minmax(220px, 1fr) 128px 170px minmax(250px, auto)")
    expect(resume).toContain("本机编辑内容会自动保留，手动保存后同步到服务端。")
    expect(applications).toContain("可直接使用上方表单新增第一条记录。")
    expect(jobs).toContain("输入具体岗位名称后开始整理能力要求。")
  })
})
