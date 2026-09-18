<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { Download, FileUp, Plus, Printer, Save, Sparkles, X } from "lucide-vue-next"

import AsyncButton from "../components/AsyncButton.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import {
  clearDraftCheckpoint,
  readDraftCheckpoint,
  writeDraftCheckpoint,
} from "../lib/draft-checkpoint"
import { exportDraft, getDraft, importResumeFile, saveDraft, type DraftRecord, type ExportFormat, type ResumeImportPreview, type ResumePayload } from "../lib/drafts"
import { toDraftSaveInput } from "../lib/draft-workflow"
import { triggerBlobDownload } from "../lib/download-file"
import { ApiRequestError } from "../lib/api"
import { getApiErrorMessage } from "../lib/api-error"
import { aiRewriteResume, computeRewriteDiff, REWRITE_INSTRUCTIONS_MAX, type RewriteMode } from "../lib/rewrite"
import { createStagedProgress } from "../composables/staged-progress"
import ResumePrintView from "../components/ResumePrintView.vue"
import {
  runPendingGuardedAction,
  resolveResumeEditorShortcutAction,
  resolveWorkspaceShortcut,
} from "../lib/keyboard-shortcuts"
import { createResumeInvalidFeedback, focusFirstInvalidResumeField } from "../lib/resume-invalid-feedback"
import { createResumeEditorOrchestration } from "../lib/resume-editor-orchestration"
import { validateDraft } from "../lib/resume-validation"

const props = defineProps<{ draftId: string }>()
const emit = defineEmits<{
  cancel: []
  saved: [draft: DraftRecord]
}>()

const loading = ref(true)
const error = ref("")
const {
  summary: invalidSummary,
  activate: activateInvalidSummary,
  sync: syncInvalidSummary,
  reset: resetInvalidSummary,
} = createResumeInvalidFeedback()

const {
  draft,
  fieldErrors,
  localSaveState,
  saving,
  isDirty,
  hydrate,
  discardLocalCheckpoint,
  save: saveEditor,
} = createResumeEditorOrchestration({
  checkpoint: (currentDraft) => writeDraftCheckpoint(window.localStorage, currentDraft),
  clearCheckpoint: (draftId) => clearDraftCheckpoint(window.localStorage, draftId),
  restoreCheckpoint: (serverDraft) => readDraftCheckpoint(window.localStorage, props.draftId, serverDraft.updatedAt),
  validate: validateDraft,
  saveRemote: (currentDraft) => saveDraft(toDraftSaveInput(currentDraft)),
  settleDraft: nextTick,
  onSaveStart: () => { error.value = "" },
  onSaved: (saved) => emit("saved", saved),
  onRemoteError: () => { error.value = "简历草稿暂未保存，请检查登录状态后重试" },
  registerBeforeUnmount: onBeforeUnmount,
})

const showLeaveConfirmation = ref(false)
const discardError = ref("")
const localSaveStatus = computed(() => {
  if (localSaveState.value === "saving") return "正在保存到本机"
  if (localSaveState.value === "error") return "本机自动保存失败，请手动保存"
  if (isDirty.value) return "已保存到本机，尚未同步"
  return "已同步到云端"
})

const skillsText = computed({
  get: () => draft.value?.resume.skills.skills.join(", ") || "",
  set: (value: string) => {
    if (draft.value) draft.value.resume.skills.skills = value.split(",").map((item) => item.trim()).filter(Boolean)
  },
})

const exportingKind = ref<ExportFormat | "">("")
const actionNotice = ref("")
const actionError = ref("")
const importing = ref(false)
const importPreview = ref<ResumeImportPreview | null>(null)
const importFileInput = ref<HTMLInputElement | null>(null)

async function ensureSavedBeforeExport(): Promise<boolean> {
  if (!isDirty.value) return true
  const result = await saveEditor()
  if (result === "invalid") {
    const currentErrors = fieldErrors.value ?? {}
    activateInvalidSummary(currentErrors)
    await nextTick()
    focusFirstInvalidResumeField(currentErrors)
    actionError.value = "简历还有必填项未补全，导出前请先修正"
    return false
  }
  if (result !== "saved") {
    actionError.value = "简历草稿暂未保存，请检查登录状态后重试"
    return false
  }
  return true
}

async function exportResume(kind: ExportFormat): Promise<void> {
  if (exportingKind.value || loading.value || importing.value || importPreview.value) return
  actionNotice.value = ""
  actionError.value = ""
  const saved = await ensureSavedBeforeExport()
  if (!saved) return
  exportingKind.value = kind
  try {
    const { filename, blob } = await exportDraft(kind, props.draftId)
    triggerBlobDownload(blob, filename)
    actionNotice.value = `已导出「${filename}」，可在浏览器下载中找到`
  } catch (caught) {
    if (caught instanceof ApiRequestError && caught.code === "pdf_renderer_unavailable") {
      // 免费托管没有云端 PDF 组件：降级为浏览器打印（可"另存为 PDF"），不把报错甩给用户。
      await openPrintPreview()
      actionNotice.value = "云端 PDF 组件不可用，已打开浏览器打印——在打印对话框选择「另存为 PDF」即可保存"
      return
    }
    actionError.value = caught instanceof Error && caught.message ? describeExportFailure(caught) : "导出失败，请稍后重试"
  } finally {
    exportingKind.value = ""
  }
}

const printOpen = ref(false)

async function openPrintPreview(): Promise<void> {
  if (!draft.value) return
  printOpen.value = true
  await nextTick()
  window.print()
  printOpen.value = false
}

function describeExportFailure(caught: Error): string {
  const message = caught.message || ""
  if (message.includes("no visible export content")) return "简历还没有可导出的内容，请先补齐姓名、联系方式、目标岗位等必填信息"
  if (message.includes("vip")) return message
  if (message.includes("超时")) return "导出耗时较长已中断，请稍后重试"
  return message.includes("暂时不可用") || message.length > 60 ? "导出服务暂时不可用，请稍后重试" : message
}

function pickImportFile(): void {
  if (importing.value || exportingKind.value || loading.value || saving.value) return
  importFileInput.value?.click()
}

async function handleImportFile(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ""
  if (!file || importing.value || !draft.value) return
  actionNotice.value = ""
  actionError.value = ""
  importing.value = true
  try {
    importPreview.value = await importResumeFile(props.draftId, file)
  } catch (caught) {
    const message = caught instanceof Error ? caught.message : ""
    actionError.value = message.includes("超时")
      ? "解析耗时较长已中断，请稍后重试"
      : message && message.length <= 80 ? message : "暂时无法解析该简历文件，请确认是 PDF 或 Word 格式后重试"
  } finally {
    importing.value = false
  }
}

function discardImportPreview(): void {
  importPreview.value = null
}

// ---------- AI 按需改写：导入/填写的简历交给 AI 润色，自定义要求可见可改 ----------
const rewritePanelOpen = ref(false)
const rewriteMode = ref<RewriteMode>("light")
const rewriteInstructions = ref("")
const rewriteLoading = ref(false)
const rewriteError = ref("")
const rewriteResult = ref<ResumePayload | null>(null)
const rewriteProgress = createStagedProgress([
  "正在理解你的改写要求",
  "正在围绕目标岗位润色表达",
  "正在核对事实一致性",
])
watch(rewriteLoading, (busy) => {
  if (busy) rewriteProgress.start()
  else rewriteProgress.stop()
})

const rewriteDiff = computed(() => {
  if (!draft.value || !rewriteResult.value) return []
  return computeRewriteDiff(draft.value.resume, rewriteResult.value)
})

function toggleRewritePanel(): void {
  if (loading.value || importing.value || importPreview.value || Boolean(exportingKind)) return
  rewritePanelOpen.value = !rewritePanelOpen.value
  if (!rewritePanelOpen.value) {
    rewriteResult.value = null
    rewriteError.value = ""
  }
}

async function runRewrite(): Promise<void> {
  if (rewriteLoading.value || !draft.value) return
  rewriteLoading.value = true
  rewriteError.value = ""
  rewriteResult.value = null
  try {
    rewriteResult.value = await aiRewriteResume({
      resume: draft.value.resume,
      roleName: draft.value.resume.job.targetRole,
      mode: rewriteMode.value,
      instructions: rewriteInstructions.value,
    })
  } catch (caught) {
    if (caught instanceof ApiRequestError && caught.code === "vip_required") {
      rewriteError.value = "深度润色是会员功能——可先使用快速润色，或在会员页升级后重试"
    } else {
      rewriteError.value = getApiErrorMessage(caught, "AI 改写暂时不可用，请稍后重试")
    }
  } finally {
    rewriteLoading.value = false
  }
}

function applyRewrite(): void {
  if (!draft.value || !rewriteResult.value) return
  draft.value.resume = rewriteResult.value
  rewriteResult.value = null
  rewritePanelOpen.value = false
  actionNotice.value = "已应用 AI 改写结果，确认无误后记得保存草稿"
}

function discardRewrite(): void {
  rewriteResult.value = null
}

async function applyImportPreview(): Promise<void> {
  if (!draft.value || !importPreview.value) return
  draft.value.resume = JSON.parse(JSON.stringify(importPreview.value.parsedResume))
  importPreview.value = null
  actionNotice.value = "已应用到当前简历，确认内容无误后记得保存"
  await nextTick()
  document.getElementById("resume-basic-name")?.focus()
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    const loaded = await getDraft(props.draftId)
    const serverDraft = JSON.parse(JSON.stringify(loaded)) as DraftRecord
    await hydrate(serverDraft)
  } catch {
    error.value = "暂时无法打开简历草稿，请稍后重试"
  } finally {
    loading.value = false
  }
}

function addEducation(): void {
  draft.value?.resume.education.push({ school: "", major: "", degree: "", startDate: "", endDate: "" })
}

function removeEducation(index: number): void {
  draft.value?.resume.education.splice(index, 1)
}

function addEmployment(): void {
  draft.value?.resume.employment.push({ company: "", position: "", startDate: "", endDate: "", description: "" })
}

function removeEmployment(index: number): void {
  draft.value?.resume.employment.splice(index, 1)
}

function addProject(): void {
  draft.value?.resume.projects.push({ name: "", role: "", startDate: "", endDate: "", description: "" })
}

function removeProject(index: number): void {
  draft.value?.resume.projects.splice(index, 1)
}

function updateCertificates(event: Event): void {
  if (!draft.value) return
  const value = (event.target as HTMLInputElement).value
  draft.value.resume.skills.certificates = value.split(",").map((item) => item.trim()).filter(Boolean)
}

async function save(): Promise<void> {
  resetInvalidSummary()
  const result = await saveEditor()
  if (result === "invalid") {
    const currentErrors = fieldErrors.value ?? {}
    activateInvalidSummary(currentErrors)
    await nextTick()
    focusFirstInvalidResumeField(currentErrors)
  }
}

function cancel(): void {
  runPendingGuardedAction(Boolean(loading.value || saving.value), () => {
    if (!isDirty.value) {
      emit("cancel")
      return
    }
    discardError.value = ""
    showLeaveConfirmation.value = true
  })
}

function continueEditing(): void {
  showLeaveConfirmation.value = false
  discardError.value = ""
  void nextTick(() => document.getElementById("resume-job-title")?.focus())
}

function discardAndReturn(): void {
  if (loading.value || saving.value) return
  try {
    discardLocalCheckpoint(props.draftId)
    showLeaveConfirmation.value = false
    emit("cancel")
  } catch {
    discardError.value = "暂时无法清除本地草稿，请重试"
  }
}

function handleBeforeUnload(event: BeforeUnloadEvent): void {
  event.preventDefault()
  event.returnValue = ""
}

function handleShortcut(event: KeyboardEvent): void {
  const action = resolveResumeEditorShortcutAction(resolveWorkspaceShortcut(event), Boolean(loading.value || saving.value))
  if (!action) return
  event.preventDefault()
  if (action === "save") void save()
  else if (action === "back") cancel()
}

watch(fieldErrors, (currentErrors) => {
  syncInvalidSummary(currentErrors ?? {})
}, { deep: true })

onMounted(() => {
  window.addEventListener("keydown", handleShortcut)
  void load()
})
watch(isDirty, (dirty) => {
  if (dirty) window.addEventListener("beforeunload", handleBeforeUnload)
  else window.removeEventListener("beforeunload", handleBeforeUnload)
})
onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleShortcut)
  window.removeEventListener("beforeunload", handleBeforeUnload)
})
</script>

<template>
  <section class="view-layout resume-editor-view">
    <div class="view-heading">
      <div>
        <h1 id="resume-editor-title">编辑简历草稿</h1>
        <p>补充真实经历与目标岗位信息，保存后可继续完善。</p>
      </div>
      <div class="heading-actions">
        <AsyncButton class="text-action" type="button" :disabled="loading || saving" :aria-disabled="loading || saving || undefined" @click="cancel"><X :size="16" aria-hidden="true" />返回草稿</AsyncButton>
        <AsyncButton class="text-action" type="button" :disabled="loading || Boolean(saving || exportingKind) || Boolean(importing) || Boolean(importPreview)" @click="pickImportFile"><FileUp :size="16" aria-hidden="true" />导入简历</AsyncButton>
        <AsyncButton class="text-action" type="button" :loading="exportingKind === 'word'" :disabled="loading || Boolean(exportingKind) || Boolean(importing) || Boolean(importPreview)" @click="exportResume('word')"><Download :size="16" aria-hidden="true" />导出 Word</AsyncButton>
        <AsyncButton class="text-action" type="button" :loading="exportingKind === 'pdf'" :disabled="loading || Boolean(exportingKind) || Boolean(importing) || Boolean(importPreview)" @click="exportResume('pdf')"><Download :size="16" aria-hidden="true" />导出 PDF</AsyncButton>
        <AsyncButton class="text-action" type="button" :disabled="loading || Boolean(exportingKind) || Boolean(importing) || Boolean(importPreview)" @click="openPrintPreview"><Printer :size="16" aria-hidden="true" />打印预览</AsyncButton>
        <AsyncButton class="text-action" type="button" :disabled="loading || Boolean(exportingKind) || Boolean(importing) || Boolean(importPreview)" @click="toggleRewritePanel"><Sparkles :size="16" aria-hidden="true" />AI 改写</AsyncButton>
        <AsyncButton class="primary-button compact" type="button" :loading="saving" :disabled="loading" @click="save"><Save :size="16" aria-hidden="true" />保存草稿</AsyncButton>
      </div>
      <input ref="importFileInput" type="file" accept=".pdf,.doc,.docx" class="visually-hidden-input" aria-hidden="true" tabindex="-1" @change="handleImportFile" />
    </div>

    <p v-if="actionNotice" class="form-success action-status" role="status" aria-live="polite">{{ actionNotice }}</p>
    <ErrorNotice v-if="actionError && (draft || loading)" :message="actionError" />

    <div v-if="rewritePanelOpen" class="rewrite-panel" role="region" aria-label="AI 按需改写">
      <div class="import-heading"><strong>AI 按需改写</strong><span class="import-filename">以当前草稿内容为基础，不虚构事实</span></div>
      <div class="rewrite-controls">
        <div class="mode-switch" role="group" aria-label="改写深度">
          <button type="button" :disabled="rewriteLoading" :class="{ 'is-selected': rewriteMode === 'light' }" @click="rewriteMode = 'light'">快速润色</button>
          <button type="button" :disabled="rewriteLoading" :class="{ 'is-selected': rewriteMode === 'deep' }" @click="rewriteMode = 'deep'">深度润色（会员）</button>
        </div>
        <label class="rewrite-instructions">
          <span>你的改写要求（可选，最多 {{ REWRITE_INSTRUCTIONS_MAX }} 字）</span>
          <textarea v-model.trim="rewriteInstructions" rows="2" :maxlength="REWRITE_INSTRUCTIONS_MAX" placeholder="例如：突出项目管理经验，量化交付成果；语气专业但不过度自信" />
        </label>
        <AsyncButton class="primary-button compact" type="button" :loading="rewriteLoading" :disabled="loading || Boolean(importing) || Boolean(importPreview)" @click="runRewrite"><Sparkles :size="16" aria-hidden="true" />{{ rewriteLoading ? "改写中" : "开始改写" }}</AsyncButton>
        <p v-if="rewriteLoading" class="staged-progress" role="status" aria-live="polite">
          <LoadingSpinner class="staged-progress-spinner" label="AI 改写进行中" />
          <span>{{ rewriteProgress.label.value }}…已等待 {{ rewriteProgress.elapsedSeconds.value }} 秒。</span>
        </p>
        <div v-if="rewriteError" class="rewrite-error-row">
          <ErrorNotice :message="rewriteError" />
          <AsyncButton v-if="!rewriteError.includes('会员')" class="text-action" type="button" :disabled="rewriteLoading" @click="runRewrite">重试</AsyncButton>
        </div>
      </div>
      <div v-if="rewriteResult" class="rewrite-diff">
        <div class="import-heading"><strong>改写预览</strong><span class="import-filename">{{ rewriteDiff.length ? `${rewriteDiff.length} 处文案变化` : "没有可预览的文案变化" }}</span></div>
        <article v-for="(entry, index) in rewriteDiff" :key="`${entry.kind}-${entry.index}`" class="rewrite-diff-entry">
          <h4>{{ entry.title }}</h4>
          <p class="diff-before"><span>改前</span>{{ entry.before || "（空）" }}</p>
          <p class="diff-after"><span>改后</span>{{ entry.after || "（空）" }}</p>
        </article>
        <div class="heading-actions import-actions">
          <AsyncButton class="text-action" type="button" @click="discardRewrite">放弃</AsyncButton>
          <AsyncButton class="primary-button compact" type="button" @click="applyRewrite">应用到当前草稿</AsyncButton>
        </div>
      </div>
    </div>

    <div v-if="importPreview" class="import-panel" role="region" aria-label="简历导入解析预览">
      <div class="import-heading"><strong>解析预览</strong><span class="import-filename">{{ importPreview.originalFilename }}</span></div>
      <p class="import-copy">请先核对以下关键信息，确认后应用到当前简历；其余内容也会一并覆盖，应用后仍需手动保存。</p>
      <div class="import-fields">
        <label><span>姓名</span><input v-model.trim="importPreview.parsedResume.basic.name" /></label>
        <label><span>手机号</span><input v-model.trim="importPreview.parsedResume.basic.phone" /></label>
        <label><span>邮箱</span><input v-model.trim="importPreview.parsedResume.basic.email" /></label>
        <label><span>目标岗位</span><input v-model.trim="importPreview.parsedResume.job.targetRole" /></label>
      </div>
      <div class="heading-actions import-actions">
        <AsyncButton class="text-action" type="button" @click="discardImportPreview">暂不应用</AsyncButton>
        <AsyncButton class="primary-button compact" type="button" @click="applyImportPreview">确认应用</AsyncButton>
      </div>
    </div>

    <div v-if="loading" class="content-skeleton editor-loading" aria-busy="true">
      <LoadingSpinner class="content-loading-spinner" label="正在读取简历草稿" />
      <span /><span /><span /><span />
    </div>
    <ErrorNotice v-else-if="error && !draft" :message="error" />
    <form v-else-if="draft" class="resume-editor-form workbench-form" novalidate @submit.prevent="save">
      <ErrorNotice v-if="error" :message="error" />
      <p v-if="invalidSummary" class="form-error validation-summary" role="alert">{{ invalidSummary }}</p>
      <section class="editor-section chapter-stage">
        <h2>基本信息</h2>
        <div class="editor-grid">
          <label>
            <span>草稿名称</span>
            <input id="resume-job-title" v-model.trim="draft.jobTitle" maxlength="160" :aria-invalid="Boolean(fieldErrors?.jobTitle)" :aria-describedby="fieldErrors?.jobTitle ? 'resume-job-title-error' : undefined" />
            <small v-if="fieldErrors?.jobTitle" id="resume-job-title-error" class="form-error">{{ fieldErrors?.jobTitle }}</small>
          </label>
          <label><span>简历模板</span><select v-model="draft.templateId"><option value="business">商务模板</option><option value="technology">技术模板</option><option value="graduate">毕业生模板</option><option value="analytics">分析模板</option></select></label>
          <label>
            <span>姓名</span>
            <input id="resume-basic-name" v-model.trim="draft.resume.basic.name" maxlength="80" :aria-invalid="Boolean(fieldErrors?.['basic.name'])" :aria-describedby="fieldErrors?.['basic.name'] ? 'resume-basic-name-error' : undefined" />
            <small v-if="fieldErrors?.['basic.name']" id="resume-basic-name-error" class="form-error">{{ fieldErrors?.["basic.name"] }}</small>
          </label>
          <label>
            <span>手机号</span>
            <input id="resume-basic-phone" v-model.trim="draft.resume.basic.phone" maxlength="30" :aria-invalid="Boolean(fieldErrors?.['basic.phone'])" :aria-describedby="fieldErrors?.['basic.phone'] ? 'resume-basic-phone-error' : undefined" />
            <small v-if="fieldErrors?.['basic.phone']" id="resume-basic-phone-error" class="form-error">{{ fieldErrors?.["basic.phone"] }}</small>
          </label>
          <label>
            <span>邮箱</span>
            <input id="resume-basic-email" v-model.trim="draft.resume.basic.email" type="email" maxlength="160" :aria-invalid="Boolean(fieldErrors?.['basic.email'])" :aria-describedby="fieldErrors?.['basic.email'] ? 'resume-basic-email-error' : undefined" />
            <small v-if="fieldErrors?.['basic.email']" id="resume-basic-email-error" class="form-error">{{ fieldErrors?.["basic.email"] }}</small>
          </label>
          <label><span>城市</span><input v-model.trim="draft.resume.basic.city" maxlength="80" /></label>
          <label>
            <span>目标岗位</span>
            <input id="resume-target-role" v-model.trim="draft.resume.job.targetRole" maxlength="120" :aria-invalid="Boolean(fieldErrors?.['job.targetRole'])" :aria-describedby="fieldErrors?.['job.targetRole'] ? 'resume-target-role-error' : undefined" />
            <small v-if="fieldErrors?.['job.targetRole']" id="resume-target-role-error" class="form-error">{{ fieldErrors?.["job.targetRole"] }}</small>
          </label>
          <label><span>期望薪资</span><input v-model.trim="draft.resume.job.expectedSalary" maxlength="80" /></label>
          <label><span>工作形式</span><input v-model.trim="draft.resume.job.employmentType" maxlength="80" /></label>
        </div>
      </section>

      <section class="editor-section chapter-stage">
        <div class="editor-section-heading"><h2>教育经历</h2><AsyncButton class="text-action compact" type="button" @click="addEducation"><Plus :size="15" aria-hidden="true" />添加教育经历</AsyncButton></div>
        <div v-for="(item, index) in draft.resume.education" :key="index" class="editor-item">
          <div class="editor-grid">
            <label><span>学校</span><input v-model.trim="item.school" /></label>
            <label><span>专业</span><input v-model.trim="item.major" /></label>
            <label><span>学位</span><input v-model.trim="item.degree" /></label>
            <label><span>起止时间</span><input v-model.trim="item.startDate" placeholder="YYYY-MM - YYYY-MM" /></label>
          </div>
          <AsyncButton class="danger-action compact" type="button" @click="removeEducation(index)">删除</AsyncButton>
        </div>
      </section>

      <section class="editor-section chapter-stage">
        <div class="editor-section-heading"><h2>工作经历</h2><AsyncButton class="text-action compact" type="button" @click="addEmployment"><Plus :size="15" aria-hidden="true" />添加工作经历</AsyncButton></div>
        <div v-for="(item, index) in draft.resume.employment" :key="index" class="editor-item">
          <div class="editor-grid">
            <label><span>公司</span><input v-model.trim="item.company" /></label>
            <label><span>职位</span><input v-model.trim="item.position" /></label>
            <label><span>起止时间</span><input v-model.trim="item.startDate" placeholder="YYYY-MM - YYYY-MM" /></label>
            <label class="editor-wide"><span>工作说明</span><textarea v-model.trim="item.description" rows="3" /></label>
          </div>
          <AsyncButton class="danger-action compact" type="button" @click="removeEmployment(index)">删除</AsyncButton>
        </div>
      </section>

      <section class="editor-section chapter-stage">
        <div class="editor-section-heading"><h2>项目经历</h2><AsyncButton class="text-action compact" type="button" @click="addProject"><Plus :size="15" aria-hidden="true" />添加项目经历</AsyncButton></div>
        <div v-for="(item, index) in draft.resume.projects" :key="index" class="editor-item">
          <div class="editor-grid">
            <label><span>项目名称</span><input v-model.trim="item.name" /></label>
            <label><span>项目角色</span><input v-model.trim="item.role" /></label>
            <label class="editor-wide"><span>项目说明</span><textarea v-model.trim="item.description" rows="3" /></label>
          </div>
          <AsyncButton class="danger-action compact" type="button" @click="removeProject(index)">删除</AsyncButton>
        </div>
      </section>

      <section class="editor-section chapter-stage">
        <h2>技能与自我评价</h2>
        <label><span>技能（用逗号分隔）</span><input v-model="skillsText" /></label>
        <label><span>证书（用逗号分隔）</span><input :value="draft.resume.skills.certificates.join(', ')" @input="updateCertificates" /></label>
        <label><span>自我评价</span><textarea v-model.trim="draft.resume.selfEvaluation" rows="5" /></label>
      </section>

      <div class="local-save-status" aria-live="polite">
        {{ localSaveStatus }}
      </div>
      <div v-if="showLeaveConfirmation" class="leave-confirmation" role="alert" aria-live="polite">
        <span>当前编辑尚未同步到云端，确定返回吗？</span>
        <div class="heading-actions">
          <AsyncButton class="text-action" type="button" @click="continueEditing">继续编辑</AsyncButton>
          <AsyncButton class="danger-action" type="button" :disabled="loading || saving" @click="discardAndReturn">放弃并返回</AsyncButton>
        </div>
        <ErrorNotice v-if="discardError" :message="discardError" />
      </div>
      <AsyncButton class="primary-button" type="submit" :loading="saving"><Save :size="17" aria-hidden="true" />保存草稿</AsyncButton>
    </form>
    <ResumePrintView v-if="draft" :resume="draft.resume" :class="{ 'is-open': printOpen }" />
  </section>
</template>
