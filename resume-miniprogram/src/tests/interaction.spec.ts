import { describe, expect, it } from "vitest"
import { existsSync, readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"

import { runWithLoading } from "../utils/async-state"
import {
  getAssessmentStepTransition,
  transitionJobRoleFeedback,
} from "../utils/h5-feedback"

describe("runWithLoading", () => {
  it("clears loading after resolve", async () => {
    const states: boolean[] = []
    await expect(runWithLoading((value) => states.push(value), async () => "ok")).resolves.toBe("ok")
    expect(states).toEqual([true, false])
  })

  it("clears loading after rejection", async () => {
    const states: boolean[] = []
    await expect(runWithLoading((value) => states.push(value), async () => { throw new Error("offline") }))
      .rejects.toThrow("offline")
    expect(states).toEqual([true, false])
  })

  it("clears loading after an abort-shaped rejection", async () => {
    const states: boolean[] = []
    await expect(runWithLoading((value) => states.push(value), async () => {
      throw new DOMException("The operation was aborted", "AbortError")
    })).rejects.toMatchObject({ name: "AbortError" })
    expect(states).toEqual([true, false])
  })

  it("transitions job feedback through invalid submission and correction", () => {
    let feedback = { error: "岗位分析失败", roleFieldError: "" }

    feedback = transitionJobRoleFeedback(feedback, { type: "submit", roles: [] })
    expect(feedback).toEqual({
      error: "",
      roleFieldError: "请输入岗位名称，或从下方联想岗位中选择。",
    })

    feedback = transitionJobRoleFeedback(feedback, { type: "input", value: " 数据工程师 " })
    expect(feedback).toEqual({ error: "", roleFieldError: "" })
  })

  it("keeps unanswered assessment steps non-blocking", () => {
    expect(getAssessmentStepTransition(0, 4, false)).toEqual({
      stepHint: "本步骤尚未作答，可继续并稍后补充",
      nextStep: 1,
      shouldSubmit: false,
    })
    expect(getAssessmentStepTransition(3, 4, false)).toEqual({
      stepHint: "本步骤尚未作答，可继续并稍后补充",
      nextStep: 3,
      shouldSubmit: true,
    })
  })

  it("clears assessment guidance after an answered step", () => {
    expect(getAssessmentStepTransition(1, 4, true)).toEqual({
      stepHint: "",
      nextStep: 2,
      shouldSubmit: false,
    })
  })

  it("keeps existing H5 async controls disabled while pending", () => {
    const assessment = readFileSync(new URL("../pages/career-assessment/index.vue", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../pages/applications/index.vue", import.meta.url), "utf8")
    const planner = readFileSync(new URL("../pages/career-planner/index.vue", import.meta.url), "utf8")
    const membership = readFileSync(new URL("../pages/membership/index.vue", import.meta.url), "utf8")
    const privacy = readFileSync(new URL("../pages/privacy/index.vue", import.meta.url), "utf8")
    const editor = readFileSync(new URL("../pages/resume-editor/index.vue", import.meta.url), "utf8")
    const jobSearch = readFileSync(new URL("../pages/job-search/index.vue", import.meta.url), "utf8")
    const jobCollection = readFileSync(new URL("../pages/job-collection/index.vue", import.meta.url), "utf8")
    const operatorKnowledge = readFileSync(new URL("../pages/operator-knowledge/index.vue", import.meta.url), "utf8")
    expect(assessment).toContain(':loading="submitting" :disabled="submitting"')
    expect(assessment).toContain("<LoadingSpinner")
    expect(applications).toContain("const timelineSaving = ref(false)")
    expect(applications).toContain("const reminderSaving = ref(false)")
    expect(applications).toContain("const pendingDeleteId = ref(\"\")")
    expect(applications).toContain(':loading="timelineSaving" :disabled="timelineSaving"')
    expect(applications).toContain(':loading="reminderSaving" :disabled="reminderSaving"')
    expect(planner).toContain(':loading="taskSaving" :disabled="taskSaving"')
    expect(planner).toContain(':loading="loading" :disabled="loading"')
    expect(membership).toContain(':loading="purchasing" :disabled="purchasing"')
    expect(membership).toContain("<LoadingSpinner")
    expect(privacy).toContain(':loading="backupBusy" :disabled="backupBusy"')
    expect(editor).toContain(':loading="importLoading" :disabled="importLoading || saveLoading || versionLoading || Boolean(versionComparingId || restoringVersionId || exporting)"')
    expect(editor).toContain(':loading="versionLoading" :disabled="versionLoading || Boolean(versionComparingId || restoringVersionId || importLoading || exporting)"')
    expect(jobSearch).toContain(':loading="marketSearchLoading" :disabled="marketSearchLoading"')
    expect(jobSearch).toContain(':loading="reviewLoading" :disabled="reviewLoading || pdfLoading"')
    expect(jobSearch).toContain(':loading="adviceLoading" :disabled="adviceLoading"')
    expect(jobCollection).toContain(':loading="saving" :disabled="saving"')
    expect(operatorKnowledge).toContain('const versionsLoading = ref("")')
    expect(operatorKnowledge).toContain("<LoadingSpinner")
    expect(operatorKnowledge).toContain(':loading="loading" :disabled="loading || Boolean(versionsLoading) || restoringVersion !== null"')
    expect(operatorKnowledge).toContain(':loading="versionsLoading === item.id"')
    expect(operatorKnowledge).toContain(':loading="restoringVersion === version.version"')
    expect(applications).toContain("if (saving.value) return")
    expect(assessment).toContain("if (submitting.value) return")
    expect(jobSearch).toContain("if (loading.value) return")
    expect(jobSearch).toContain("if (marketSearchLoading.value || !activeRoleName.value) return")
    expect(jobSearch).toContain("if (reviewLoading.value || pdfLoading.value) return")
    expect(jobSearch).toContain("if (adviceLoading.value) return")
    expect(membership).toContain("if (purchasing.value) return")
  })

  it("locks cross-action login and resume version requests while pending", () => {
    const login = readFileSync(new URL("../pages/login/index.vue", import.meta.url), "utf8")
    const editor = readFileSync(new URL("../pages/resume-editor/index.vue", import.meta.url), "utf8")
    const collection = readFileSync(new URL("../pages/job-collection/index.vue", import.meta.url), "utf8")
    expect(login).toContain(':loading="sending" :disabled="sending || loggingIn"')
    expect(login).toContain(':loading="loggingIn" :disabled="loggingIn || sending"')
    expect(login).toContain(':disabled="passwordAction !== null || sending || loggingIn"')
    expect(editor).toContain('const versionComparingId = ref("")')
    expect(editor).toContain(':loading="versionComparingId === version.id"')
    expect(editor).toContain(':loading="restoringVersionId === version.id"')
    expect(editor).toContain('if (exporting.value || saveLoading.value || importLoading.value || versionLoading.value || versionComparingId.value || restoringVersionId.value) return')
    expect(collection).toContain("if (removingFavoriteId.value || subscriptionSaving.value) return")
  })

  it("centralizes H5 error and disabled-state presentation", () => {
    const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
    const login = readFileSync(new URL("../pages/login/index.vue", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../pages/applications/index.vue", import.meta.url), "utf8")
    expect(app).toContain("--ui-error-bg")
    expect(app).toContain("button:disabled")
    expect(app).toContain("background-color: var(--ui-disabled-bg) !important")
    expect(app).toContain(".ui-error-tip")
    expect(login).toContain("ui-error-tip")
    expect(applications).toContain("ui-error-tip")
  })

  it("contains off-screen H5 long-list items without changing list data", () => {
    const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../pages/applications/index.vue", import.meta.url), "utf8")
    const evidence = readFileSync(new URL("../pages/evidence/index.vue", import.meta.url), "utf8")
    const jobs = readFileSync(new URL("../pages/job-search/index.vue", import.meta.url), "utf8")
    expect(app).toContain(".ui-long-list-item")
    expect(app).toContain("content-visibility: auto")
    expect(app).toContain("contain-intrinsic-size")
    expect(applications).toContain("ui-long-list-item")
    expect(evidence).toContain("ui-long-list-item")
    expect(jobs).toContain("ui-long-list-item")
  })

  it("exposes H5 form, action, and overlay accessibility semantics", () => {
    const field = readFileSync(new URL("../components/FormField.vue", import.meta.url), "utf8")
    const onboarding = readFileSync(new URL("../components/OnboardingTour.vue", import.meta.url), "utf8")
    const jobs = readFileSync(new URL("../pages/job-search/index.vue", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../pages/applications/index.vue", import.meta.url), "utf8")

    expect(field).toContain(':aria-label="label"')
    expect(field).toContain(':aria-invalid="Boolean(error)"')
    expect(field).toContain(':aria-describedby="error ? errorId : undefined"')
    expect(field).toContain("getCurrentInstance")
    expect(field).not.toContain("useId")
    expect(onboarding).toContain('@tap="closeFromMask"')
    expect(onboarding).toContain("@tap.stop")
    expect(jobs).toContain('role="button"')
    expect(jobs).toContain('tabindex="0"')
    expect(jobs).toContain(':aria-expanded="isAnalysisSectionOpen(section.order)"')
    expect(applications).toContain(':aria-label="`删除 ${item.company} 的 ${item.roleName} 投递记录`"')
  })

  it("wires H5 resume resilience and mapped field errors", () => {
    const resumeForm = readFileSync(new URL("../pages/resume-form/index.vue", import.meta.url), "utf8")
    expect(resumeForm).toContain("createResumeFormOrchestration")
    expect(resumeForm).toContain("registerHide: onHide")
    expect(resumeForm).toContain("registerBeforeUnmount: onBeforeUnmount")
    expect(resumeForm).toContain("saveRemote: () => saveDraft")
    expect(resumeForm).toContain("settleSavedId: nextTick")
    expect(resumeForm).toContain(':error="fieldErrors[\'basic.name\']"')
    expect(resumeForm).toContain(':error="fieldErrors[\'basic.phone\']"')
    expect(resumeForm).toContain(':error="fieldErrors[\'basic.email\']"')
    expect(resumeForm).toContain(':error="fieldErrors[\'job.targetRole\']"')
    expect(resumeForm).not.toContain("if (errors.length) return\n  if (errors.length)")
  })

  it("keeps resume-form checkpoint persistence inside the caught orchestrator boundary", () => {
    const resumeForm = readFileSync(new URL("../pages/resume-form/index.vue", import.meta.url), "utf8")

    expect(resumeForm.match(/store\.checkpoint\(\)/g)).toHaveLength(1)
    expect(resumeForm).toContain("checkpoint: () => store.checkpoint()")
    expect(resumeForm).toContain("store.applyEvidenceSuggestion(suggestion, false)")
    expect(resumeForm).toContain("flushLocalCheckpoint")
    expect(resumeForm).toMatch(/prepareResumeForJob[\s\S]*await nextTick\(\)[\s\S]*flushLocalCheckpoint\(\)[\s\S]*uni\.navigateTo/)
  })

  it("uses the accessible H5 long-text contract", () => {
    const componentUrl = new URL("../components/ExpandableText.vue", import.meta.url)
    expect(existsSync(fileURLToPath(componentUrl))).toBe(true)
    const component = readFileSync(componentUrl, "utf8")
    const applications = readFileSync(new URL("../pages/applications/index.vue", import.meta.url), "utf8")
    const collection = readFileSync(new URL("../pages/job-collection/index.vue", import.meta.url), "utf8")
    const jobs = readFileSync(new URL("../pages/job-search/index.vue", import.meta.url), "utf8")
    const preview = readFileSync(new URL("../components/ResumePreview.vue", import.meta.url), "utf8")
    expect(component).toContain(':aria-expanded="expanded"')
    expect(component).toContain("getCurrentInstance")
    expect(component).not.toContain("useId")
    expect(component).toContain("watch(() => props.text")
    expect(component).toContain("-webkit-line-clamp")
    expect(component).toContain("overflow-wrap: anywhere")
    expect(component).toContain("展开")
    expect(component).toContain("收起")
    expect(applications).toContain('<ExpandableText class="record-role"')
    expect(collection).toContain('<ExpandableText class="role"')
    expect(jobs).toContain('<ExpandableText class="role"')
    expect(preview).toContain(':expand-at="96"')
  })

  it("separates H5 field feedback and restores focus after native modals", () => {
    const jobSearch = readFileSync(new URL("../pages/job-search/index.vue", import.meta.url), "utf8")
    const assessment = readFileSync(new URL("../pages/career-assessment/index.vue", import.meta.url), "utf8")
    const editor = readFileSync(new URL("../pages/resume-editor/index.vue", import.meta.url), "utf8")
    expect(jobSearch).toContain('const roleFieldError = ref("")')
    expect(jobSearch).toContain(':aria-invalid="Boolean(roleFieldError)"')
    expect(jobSearch).toContain('id="job-role-error"')
    expect(jobSearch.match(/transitionJobRoleFeedback/g)).toHaveLength(3)
    expect(assessment).toContain('const stepHint = ref("")')
    expect(assessment).toContain('aria-live="polite"')
    expect(editor.match(/const restoreFocus = captureFocusRestore/g)).toHaveLength(2)
    expect(editor.match(/typeof document === "undefined" \? undefined : document/g)).toHaveLength(2)
    expect(editor.match(/complete: restoreFocus/g)).toHaveLength(2)
  })

  it("bounds H5 long lists and adds additive empty states", () => {
    const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
    const drafts = readFileSync(new URL("../pages/drafts/index.vue", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../pages/applications/index.vue", import.meta.url), "utf8")
    const evidence = readFileSync(new URL("../pages/evidence/index.vue", import.meta.url), "utf8")
    const collection = readFileSync(new URL("../pages/job-collection/index.vue", import.meta.url), "utf8")
    const jobSearch = readFileSync(new URL("../pages/job-search/index.vue", import.meta.url), "utf8")
    const progressiveScrollRoot = '<scroll-view class="page progressive-scroll-page" scroll-y @scrolltolower="showMore">'
    const editableProgressiveScrollRoot = '<scroll-view class="page progressive-scroll-page" scroll-y :scroll-top="pageScrollTop" @scroll="pageScrollTop = $event.detail.scrollTop" @scrolltolower="showMore">'
    for (const page of [drafts, collection]) {
      expect(page).toContain("useIncrementalList")
      expect(page).toContain(progressiveScrollRoot)
      expect(page).toContain('v-for="item in renderedItems"')
    }
    for (const page of [applications, evidence]) {
      expect(page).toContain("useIncrementalList")
      expect(page).toContain(editableProgressiveScrollRoot)
      expect(page).toContain('v-for="item in renderedItems"')
    }
    expect(drafts).not.toContain('v-for="item in drafts"')
    expect(drafts).toContain('class="draft ui-long-list-item"')
    expect(applications).not.toContain('v-for="item in visibleApplications"')
    expect(evidence).not.toContain('v-for="item in evidence"')
    expect(collection).not.toContain('v-for="item in favorites"')
    expect(drafts).toContain("progressive-scroll-page")
    expect(app).toContain("contain-intrinsic-size: auto 180rpx")
    expect(app).toContain(".progressive-scroll-page")
    expect(jobSearch).toContain("job-empty-state")
    expect(drafts).toContain("本机填写中的内容也会自动保留。")
    expect(drafts).toContain('/pages/resume-form/index')
    expect(applications).toContain("可先查询岗位，再回到这里记录进度。")
    expect(applications).toContain('/pages/job-search/index')
    expect(jobSearch).toContain("暂未找到匹配岗位，可换一个更具体的岗位名称。")
  })

  it("returns fixed-scroll H5 editors to their forms", () => {
    const applications = readFileSync(new URL("../pages/applications/index.vue", import.meta.url), "utf8")
    const evidence = readFileSync(new URL("../pages/evidence/index.vue", import.meta.url), "utf8")
    for (const page of [applications, evidence]) {
      const editSection = page.match(/function edit\([^]*?\r?\n}\r?\n/)?.[0] ?? ""
      expect(page).toContain("const pageScrollTop = ref(0)")
      expect(editSection).toContain("pageScrollTop.value = 0")
      expect(editSection).not.toContain("uni.pageScrollTo")
    }
  })
})
