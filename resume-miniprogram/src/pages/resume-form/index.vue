<script setup lang="ts">
import { onHide } from "@dcloudio/uni-app"
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue"

import FormField from "../../components/FormField.vue"
import LoadingSpinner from "../../components/LoadingSpinner.vue"
import { getEvidenceSuggestions } from "../../services/evidence-api"
import { aiRewriteResume, saveDraft, type RewriteMode } from "../../services/resume-api"
import { toUserMessage } from "../../services/http"
import { useResumeStore } from "../../stores/resume"
import { getClientId } from "../../stores/session"
import type { EvidenceSuggestion } from "../../types/evidence"
import type { ResumePayload } from "../../types/resume"
import {
  createRoleBasedInternshipDraft,
  createRoleBasedProjectDraft,
  prepareResumeForJob,
} from "../../utils/resume-autofill"
import { createResumeFormOrchestration } from "../../utils/resume-form-orchestration"
import { toValidationErrorMap, validateResume } from "../../utils/validators"

const store = useResumeStore()
const resume = computed(() => store.draft.resume)
const activeJob = computed(() => store.activeJob ?? store.draft.jobIntelligence)
const evidenceSuggestions = ref<EvidenceSuggestion[]>([])
const suggestionsLoading = ref(false)
watch(activeJob, (job) => {
  evidenceSuggestions.value = []
  if (job) void loadEvidenceSuggestions(job.roleName)
}, { immediate: true })

const {
  localSaveState,
  fieldErrors,
  saving,
  flushLocalCheckpoint,
  save: saveResume,
} = createResumeFormOrchestration({
  draft: () => store.draft,
  resume,
  checkpoint: () => store.checkpoint(),
  validate: () => toValidationErrorMap(validateResume(resume.value)),
  saveRemote: () => saveDraft(getClientId(), store.draft),
  applySavedId: (id) => { store.draft.id = id },
  settleSavedId: nextTick,
  registerHide: onHide,
  registerBeforeUnmount: onBeforeUnmount,
})

function addEducation() {
  resume.value.education.push({ school: "", major: "", degree: "", startDate: "", endDate: "", courses: "" })
}

function addEmployment() {
  resume.value.employment.push({ company: "", position: "", startDate: "", endDate: "", description: "" })
}

function addProject() {
  resume.value.projects.push({ name: "", role: "", startDate: "", endDate: "", description: "" })
}

function addSuggestedProject() {
  if (!activeJob.value) return
  resume.value.projects.push(createRoleBasedProjectDraft(activeJob.value))
  uni.showToast({ title: "已添加项目草案，请补全真实信息", icon: "none" })
}

function addSuggestedInternship() {
  if (!activeJob.value) return
  resume.value.employment.push(createRoleBasedInternshipDraft(activeJob.value))
  uni.showToast({ title: "已添加实习草案，请替换待确认信息", icon: "none" })
}

// ---------- AI 按需改写 ----------
const REWRITE_INSTRUCTIONS_MAX = 200
const rewriteOpen = ref(false)
const rewriteMode = ref<RewriteMode>("light")
const rewriteInstructions = ref("")
const rewriteLoading = ref(false)
const rewriteError = ref("")
const rewriteResult = ref<ResumePayload | null>(null)
const rewriteSnapshot = ref<ResumePayload | null>(null)

const rewriteDiff = computed(() => {
  if (!rewriteSnapshot.value || !rewriteResult.value) return []
  const entries: Array<{ title: string; before: string; after: string }> = []
  rewriteResult.value.employment.forEach((item, index) => {
    const old = rewriteSnapshot.value?.employment[index]
    if (old && old.description !== item.description) {
      entries.push({ title: [item.company, item.position].filter(Boolean).join(" · ") || "工作经历", before: old.description, after: item.description })
    }
  })
  rewriteResult.value.projects.forEach((item, index) => {
    const old = rewriteSnapshot.value?.projects[index]
    if (old && old.description !== item.description) {
      entries.push({ title: item.name || "项目", before: old.description, after: item.description })
    }
  })
  if (rewriteSnapshot.value.selfEvaluation !== rewriteResult.value.selfEvaluation) {
    entries.push({ title: "自我评价", before: rewriteSnapshot.value.selfEvaluation, after: rewriteResult.value.selfEvaluation })
  }
  return entries
})

function openRewrite() {
  if (saving.value || rewriteLoading.value) return
  rewriteSnapshot.value = JSON.parse(JSON.stringify(resume.value)) as ResumePayload
  rewriteError.value = ""
  rewriteResult.value = null
  rewriteOpen.value = true
}

function closeRewrite() {
  if (rewriteLoading.value) return
  rewriteOpen.value = false
}

async function runRewrite() {
  if (rewriteLoading.value) return
  rewriteLoading.value = true
  rewriteError.value = ""
  rewriteResult.value = null
  try {
    rewriteResult.value = await aiRewriteResume(
      resume.value,
      activeJob.value?.roleName || "",
      rewriteMode.value,
      rewriteInstructions.value || undefined,
    )
  } catch (reason) {
    rewriteError.value = toUserMessage(reason, "AI 改写暂时不可用，请稍后重试。")
  } finally {
    rewriteLoading.value = false
  }
}

function applyRewrite() {
  if (!rewriteResult.value) return
  store.draft.resume = rewriteResult.value
  rewriteOpen.value = false
  uni.showToast({ title: "已应用改写，记得保存草稿", icon: "none" })
}

async function loadEvidenceSuggestions(roleName: string) {
  suggestionsLoading.value = true
  try {
    evidenceSuggestions.value = await getEvidenceSuggestions(getClientId(), roleName)
  } catch {
    evidenceSuggestions.value = []
  } finally {
    suggestionsLoading.value = false
  }
}

function openEvidenceLibrary() {
  uni.navigateTo({ url: "/pages/evidence/index" })
}

function applyEvidenceSuggestion(suggestion: EvidenceSuggestion) {
  if (!store.applyEvidenceSuggestion(suggestion, false)) {
    uni.showToast({ title: "已有对应经历，不会覆盖", icon: "none" })
    return
  }
  uni.showToast({ title: "已写入空白经历，请补充待确认信息", icon: "success" })
}

async function save() {
  const result = await saveResume()
  if (result === "saved") {
    uni.showToast({ title: "草稿已保存", icon: "success" })
  } else if (result === "local-fallback") {
    uni.showToast({ title: "网络异常，已保留本地草稿", icon: "none" })
  }
}

async function prepareAndChooseTemplate() {
  const job = activeJob.value
  if (!job) {
    uni.showToast({ title: "请先查询并选择目标岗位", icon: "none" })
    return
  }
  prepareResumeForJob(store.draft, job)
  await nextTick()
  flushLocalCheckpoint()
  uni.navigateTo({ url: "/pages/template-picker/index" })
}
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view v-if="Object.keys(fieldErrors).length" class="validation-summary">
      <text v-for="(message, field) in fieldErrors" :key="field">{{ message }}</text>
    </view>
    <view class="card">
      <text class="heading">个人信息</text>
      <FormField label="姓名" v-model="resume.basic.name" placeholder="请输入姓名" :error="fieldErrors['basic.name']" />
      <FormField label="手机号码" v-model="resume.basic.phone" placeholder="请输入手机号码" :error="fieldErrors['basic.phone']" />
      <FormField label="邮箱" v-model="resume.basic.email" placeholder="请输入邮箱" :error="fieldErrors['basic.email']" />
      <FormField label="所在城市" v-model="resume.basic.city" placeholder="请输入城市" />
    </view>

    <view class="card">
      <text class="heading">求职信息</text>
      <FormField label="期望岗位" v-model="resume.job.targetRole" placeholder="例如：数据工程师" :error="fieldErrors['job.targetRole']" />
      <FormField label="期望薪资" v-model="resume.job.expectedSalary" placeholder="例如：20k-30k" />
      <FormField label="到岗时间" v-model="resume.job.availability" placeholder="例如：两周内" />
    </view>

    <view v-if="activeJob" class="card enrichment-card">
      <text class="heading">AI 补全草案</text>
      <text class="enrichment-hint">当前目标：{{ activeJob.roleName }}。智能补全会在空白经历中生成 2 个项目草案和 1 个实习草案；所有 [待确认] 内容必须替换成真实经历、公司、时间与证据。</text>
      <view class="enrichment-actions">
        <button class="secondary" @click="addSuggestedProject">添加项目经历草案</button>
        <button class="primary" @click="addSuggestedInternship">添加实习经历草案</button>
      </view>
      <view class="evidence-entry">
        <view>
          <text class="evidence-entry-title">经历证据库</text>
          <text class="evidence-entry-hint">先录入真实经历，再按当前岗位生成可确认草案。</text>
        </view>
        <button size="mini" class="secondary" @click="openEvidenceLibrary">管理经历</button>
      </view>
      <LoadingSpinner v-if="suggestionsLoading" size="sm" label="正在读取经历建议" />
      <view v-else-if="evidenceSuggestions.length" class="suggestion-list">
        <view
          v-for="suggestion in evidenceSuggestions"
          :key="suggestion.sourceEvidenceId"
          class="suggestion-card"
        >
          <view class="suggestion-top">
            <text>{{ suggestion.sourceTitle }}</text>
            <text>{{ suggestion.targetSection === "project" ? "项目经历" : "实习/工作经历" }}</text>
          </view>
          <text class="suggestion-description">{{ suggestion.description }}</text>
          <text v-if="suggestion.riskNote" class="suggestion-risk">{{ suggestion.riskNote }}</text>
          <button size="mini" class="secondary" @click="applyEvidenceSuggestion(suggestion)">写入空白区</button>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="row">
        <text class="heading">教育经历</text>
        <button size="mini" @click="addEducation">新增</button>
      </view>
      <view v-for="(item, index) in resume.education" :key="index" class="entry">
        <FormField label="学校" v-model="item.school" />
        <FormField label="专业" v-model="item.major" />
        <button size="mini" @click="resume.education.splice(index, 1)">删除</button>
      </view>
    </view>

    <view class="card">
      <view class="row">
        <text class="heading">实习/工作经历</text>
        <button size="mini" @click="addEmployment">新增</button>
      </view>
      <view v-for="(item, index) in resume.employment" :key="index" class="entry">
        <FormField label="公司" v-model="item.company" />
        <FormField label="岗位" v-model="item.position" />
        <textarea v-model="item.description" placeholder="工作描述" />
        <button size="mini" @click="resume.employment.splice(index, 1)">删除</button>
      </view>
    </view>

    <view class="card">
      <view class="row">
        <text class="heading">项目经历</text>
        <button size="mini" @click="addProject">新增</button>
      </view>
      <view v-for="(item, index) in resume.projects" :key="index" class="entry">
        <FormField label="项目名称" v-model="item.name" />
        <FormField label="角色" v-model="item.role" />
        <textarea v-model="item.description" placeholder="项目描述与成果" />
        <button size="mini" @click="resume.projects.splice(index, 1)">删除</button>
      </view>
    </view>

    <view class="card">
      <FormField
        label="技能（以逗号分隔）"
        :model-value="resume.skills.skills.join(',')"
        @update:model-value="resume.skills.skills = $event.split(',').map(item => item.trim()).filter(Boolean)"
      />
      <textarea v-model="resume.selfEvaluation" placeholder="自我评价" />
    </view>

    <text class="local-save-status" aria-live="polite">
      {{ localSaveState === "saving" ? "正在保存到本机" : localSaveState === "saved" ? "已保存到本机" : localSaveState === "error" ? "本机自动保存失败，请手动保存" : "" }}
    </text>
    <view class="actions">
      <button :loading="saving" :disabled="saving" @click="save">保存草稿</button>
      <button class="secondary" :disabled="saving" @click="openRewrite">AI 改写</button>
      <button class="primary" @click="prepareAndChooseTemplate">智能补全并选择模板</button>
    </view>

    <view v-if="rewriteOpen" class="rewrite-mask" @click="closeRewrite">
      <view class="rewrite-sheet" @click.stop>
        <text class="rewrite-title">AI 按需改写</text>
        <text class="rewrite-hint">以当前草稿为底稿润色表达，不虚构任何事实。</text>
        <view class="rewrite-modes">
          <button size="mini" :class="{ 'mode-active': rewriteMode === 'light' }" :disabled="rewriteLoading" @click="rewriteMode = 'light'">快速润色</button>
          <button size="mini" :class="{ 'mode-active': rewriteMode === 'deep' }" :disabled="rewriteLoading" @click="rewriteMode = 'deep'">深度润色（会员）</button>
        </view>
        <textarea
          v-model="rewriteInstructions"
          class="rewrite-input"
          :maxlength="REWRITE_INSTRUCTIONS_MAX"
          placeholder="你的要求（可选）：例如突出项目管理经验、量化交付成果"
        />
        <button v-if="!rewriteResult" class="primary" :loading="rewriteLoading" :disabled="rewriteLoading" @click="runRewrite">
          {{ rewriteLoading ? "改写中，约需 30-90 秒" : "开始改写" }}
        </button>
        <text v-if="rewriteError" class="rewrite-error">{{ rewriteError }}</text>
        <view v-if="rewriteResult" class="rewrite-preview">
          <text class="rewrite-preview-title">改写预览（{{ rewriteDiff.length }} 处变化）</text>
          <view v-for="(entry, index) in rewriteDiff" :key="index" class="rewrite-diff-entry">
            <text class="rewrite-diff-title">{{ entry.title }}</text>
            <text class="diff-before">改前：{{ entry.before || "（空）" }}</text>
            <text class="diff-after">改后：{{ entry.after || "（空）" }}</text>
          </view>
          <text v-if="!rewriteDiff.length" class="rewrite-hint">本次没有产生文案变化。</text>
          <view class="rewrite-actions">
            <button size="mini" :disabled="rewriteLoading" @click="closeRewrite">放弃</button>
            <button size="mini" class="primary" @click="applyRewrite">应用到草稿</button>
          </view>
        </view>
        <button v-if="!rewriteResult" size="mini" class="secondary" :disabled="rewriteLoading" @click="closeRewrite">关闭</button>
      </view>
    </view>
  </scroll-view>
</template>

<style scoped>
.page { height: 100vh; padding: 24rpx; box-sizing: border-box; background: #f7f8fa; }
.card { margin-bottom: 20rpx; padding: 24rpx; background: #fff; border: 1rpx solid #e5e6eb; border-radius: 16rpx; }
.heading { font-size: 32rpx; font-weight: 600; color: #1f2329; }
.row { display: flex; justify-content: space-between; align-items: center; }
.entry { margin-top: 18rpx; padding-top: 12rpx; border-top: 1px solid #f2f3f5; }
textarea { width: 100%; min-height: 130rpx; margin: 16rpx 0; padding: 16rpx; box-sizing: border-box; color: #4e5969; background: #f7f8fa; border-radius: 12rpx; }
.actions { display: flex; gap: 16rpx; padding-bottom: 48rpx; }.actions button { flex: 1; }
.primary { color: #fff; background: #2563eb; }.secondary { color: #4e5969; background: #f2f3f5; }
.enrichment-card { background: #f7faff; border-color: #b7d8ff; }
.enrichment-hint { display: block; margin-top: 14rpx; color: #4e5969; line-height: 1.6; }
.enrichment-actions { display: flex; gap: 16rpx; margin-top: 20rpx; }.enrichment-actions button { flex: 1; font-size: 24rpx; }
.evidence-entry { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; margin-top: 22rpx; padding: 18rpx; background: #eef6ff; border: 1rpx solid #cfe4ff; border-radius: 14rpx; }
.evidence-entry-title, .evidence-entry-hint { display: block; }.evidence-entry-title { color: #1d4ed8; font-size: 25rpx; font-weight: 700; }.evidence-entry-hint { margin-top: 5rpx; color: #66788b; font-size: 21rpx; }.evidence-entry button { flex-shrink: 0; }
.suggestion-list { margin-top: 16rpx; }.suggestion-card { margin-top: 12rpx; padding: 16rpx; background: #fff; border: 1rpx solid #d8e8f8; border-radius: 12rpx; }
.suggestion-top { display: flex; align-items: center; justify-content: space-between; gap: 12rpx; color: #1d4ed8; font-size: 24rpx; font-weight: 700; }.suggestion-top text:last-child { color: #86909c; font-size: 20rpx; font-weight: 400; }
.suggestion-description, .suggestion-risk { display: block; margin-top: 10rpx; color: #4e5969; font-size: 22rpx; line-height: 1.55; white-space: pre-line; }.suggestion-risk { color: #b26a00; }.suggestion-card button { margin-top: 12rpx; }
.validation-summary { margin-bottom: 20rpx; padding: 16rpx 20rpx; color: #b42318; background: #fdf1ef; border: 1rpx solid #ffccc7; border-radius: 12rpx; }.validation-summary text { display: block; font-size: 23rpx; line-height: 1.55; }
.local-save-status { display: block; min-height: 34rpx; margin-bottom: 12rpx; color: #66788b; font-size: 22rpx; text-align: right; }
.rewrite-mask { position: fixed; inset: 0; z-index: 30; display: flex; align-items: flex-end; background: rgba(15, 23, 42, 0.45); }
.rewrite-sheet { width: 100%; box-sizing: border-box; max-height: 82vh; overflow-y: auto; padding: 28rpx 28rpx 44rpx; background: #fff; border-radius: 24rpx 24rpx 0 0; display: flex; flex-direction: column; gap: 16rpx; }
.rewrite-title { font-size: 32rpx; font-weight: 700; color: #1f2329; }
.rewrite-hint { color: #66788b; font-size: 23rpx; line-height: 1.6; }
.rewrite-modes { display: flex; gap: 14rpx; }.rewrite-modes button { flex: 1; font-size: 24rpx; }
.mode-active { color: #1d4ed8; background: #e8efff; border: 1rpx solid #b7d8ff; }
.rewrite-input { width: 100%; min-height: 120rpx; padding: 16rpx; box-sizing: border-box; color: #4e5969; background: #f7f8fa; border-radius: 12rpx; }
.rewrite-error { color: #bf3f3a; font-size: 23rpx; line-height: 1.55; }
.rewrite-preview { display: flex; flex-direction: column; gap: 14rpx; padding: 18rpx; background: #f7f8fa; border-radius: 14rpx; }
.rewrite-preview-title { font-size: 26rpx; font-weight: 700; color: #1f2329; }
.rewrite-diff-entry { padding: 14rpx; background: #fff; border: 1rpx solid #e5e6eb; border-radius: 12rpx; }
.rewrite-diff-title { display: block; font-size: 24rpx; font-weight: 700; color: #1f2329; }
.diff-before { display: block; margin-top: 8rpx; color: #8a4a44; font-size: 22rpx; line-height: 1.55; }
.diff-after { display: block; margin-top: 6rpx; color: #16604a; font-size: 22rpx; line-height: 1.55; }
.rewrite-actions { display: flex; gap: 14rpx; margin-top: 6rpx; }.rewrite-actions button { flex: 1; }
</style>
