<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { Plus, Save, X } from "lucide-vue-next"

import AsyncButton from "../components/AsyncButton.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import {
  clearDraftCheckpoint,
  readDraftCheckpoint,
  writeDraftCheckpoint,
} from "../lib/draft-checkpoint"
import { getDraft, saveDraft, type DraftRecord } from "../lib/drafts"
import { toDraftSaveInput } from "../lib/draft-workflow"
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
  hydrate,
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

const skillsText = computed({
  get: () => draft.value?.resume.skills.skills.join(", ") || "",
  set: (value: string) => {
    if (draft.value) draft.value.resume.skills.skills = value.split(",").map((item) => item.trim()).filter(Boolean)
  },
})

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
    activateInvalidSummary(fieldErrors.value)
    await nextTick()
    focusFirstInvalidResumeField(fieldErrors.value)
  }
}

function cancel(): void {
  runPendingGuardedAction(loading.value || saving.value, () => emit("cancel"))
}

function handleShortcut(event: KeyboardEvent): void {
  const action = resolveResumeEditorShortcutAction(resolveWorkspaceShortcut(event), loading.value || saving.value)
  if (!action) return
  event.preventDefault()
  if (action === "save") void save()
  else if (action === "back") cancel()
}

watch(fieldErrors, (currentErrors) => {
  syncInvalidSummary(currentErrors)
}, { deep: true })

onMounted(() => {
  window.addEventListener("keydown", handleShortcut)
  void load()
})
onBeforeUnmount(() => window.removeEventListener("keydown", handleShortcut))
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
        <AsyncButton class="primary-button compact" type="button" :loading="saving" :disabled="loading" @click="save"><Save :size="16" aria-hidden="true" />保存草稿</AsyncButton>
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
            <input id="resume-job-title" v-model.trim="draft.jobTitle" maxlength="160" :aria-invalid="Boolean(fieldErrors.jobTitle)" :aria-describedby="fieldErrors.jobTitle ? 'resume-job-title-error' : undefined" />
            <small v-if="fieldErrors.jobTitle" id="resume-job-title-error" class="form-error">{{ fieldErrors.jobTitle }}</small>
          </label>
          <label><span>简历模板</span><select v-model="draft.templateId"><option value="business">商务模板</option><option value="technology">技术模板</option><option value="graduate">毕业生模板</option><option value="analytics">分析模板</option></select></label>
          <label>
            <span>姓名</span>
            <input id="resume-basic-name" v-model.trim="draft.resume.basic.name" maxlength="80" :aria-invalid="Boolean(fieldErrors['basic.name'])" :aria-describedby="fieldErrors['basic.name'] ? 'resume-basic-name-error' : undefined" />
            <small v-if="fieldErrors['basic.name']" id="resume-basic-name-error" class="form-error">{{ fieldErrors["basic.name"] }}</small>
          </label>
          <label>
            <span>手机号</span>
            <input id="resume-basic-phone" v-model.trim="draft.resume.basic.phone" maxlength="30" :aria-invalid="Boolean(fieldErrors['basic.phone'])" :aria-describedby="fieldErrors['basic.phone'] ? 'resume-basic-phone-error' : undefined" />
            <small v-if="fieldErrors['basic.phone']" id="resume-basic-phone-error" class="form-error">{{ fieldErrors["basic.phone"] }}</small>
          </label>
          <label>
            <span>邮箱</span>
            <input id="resume-basic-email" v-model.trim="draft.resume.basic.email" type="email" maxlength="160" :aria-invalid="Boolean(fieldErrors['basic.email'])" :aria-describedby="fieldErrors['basic.email'] ? 'resume-basic-email-error' : undefined" />
            <small v-if="fieldErrors['basic.email']" id="resume-basic-email-error" class="form-error">{{ fieldErrors["basic.email"] }}</small>
          </label>
          <label><span>城市</span><input v-model.trim="draft.resume.basic.city" maxlength="80" /></label>
          <label>
            <span>目标岗位</span>
            <input id="resume-target-role" v-model.trim="draft.resume.job.targetRole" maxlength="120" :aria-invalid="Boolean(fieldErrors['job.targetRole'])" :aria-describedby="fieldErrors['job.targetRole'] ? 'resume-target-role-error' : undefined" />
            <small v-if="fieldErrors['job.targetRole']" id="resume-target-role-error" class="form-error">{{ fieldErrors["job.targetRole"] }}</small>
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
        {{ localSaveState === "saving" ? "正在保存到本机" : localSaveState === "saved" ? "已保存到本机" : localSaveState === "error" ? "本机自动保存失败，请手动保存" : "" }}
      </div>
      <AsyncButton class="primary-button" type="submit" :loading="saving"><Save :size="17" aria-hidden="true" />保存草稿</AsyncButton>
    </form>
  </section>
</template>
