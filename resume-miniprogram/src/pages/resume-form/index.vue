<script setup lang="ts">
import { onHide } from "@dcloudio/uni-app"
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue"

import FormField from "../../components/FormField.vue"
import LoadingSpinner from "../../components/LoadingSpinner.vue"
import { getEvidenceSuggestions } from "../../services/evidence-api"
import { saveDraft } from "../../services/resume-api"
import { useResumeStore } from "../../stores/resume"
import { getClientId } from "../../stores/session"
import type { EvidenceSuggestion } from "../../types/evidence"
import { createDebouncedTask } from "../../utils/debounced-task"
import {
  createRoleBasedInternshipDraft,
  createRoleBasedProjectDraft,
  prepareResumeForJob,
} from "../../utils/resume-autofill"
import { toValidationErrorMap, validateResume } from "../../utils/validators"

const store = useResumeStore()
const resume = computed(() => store.draft.resume)
const activeJob = computed(() => store.activeJob ?? store.draft.jobIntelligence)
const evidenceSuggestions = ref<EvidenceSuggestion[]>([])
const suggestionsLoading = ref(false)
const fieldErrors = ref<Record<string, string>>({})
const saving = ref(false)
const localSaveState = ref<"idle" | "saving" | "saved" | "error">("idle")
const validationActive = ref(false)
let checkpointPaused = false

function persistLocalCheckpoint(): void {
  try {
    store.checkpoint()
    localSaveState.value = "saved"
  } catch {
    localSaveState.value = "error"
  }
}

const localCheckpoint = createDebouncedTask(persistLocalCheckpoint, 800)

watch(() => store.draft, () => {
  if (checkpointPaused) return
  localSaveState.value = "saving"
  localCheckpoint.schedule()
}, { deep: true })
watch(activeJob, (job) => {
  evidenceSuggestions.value = []
  if (job) void loadEvidenceSuggestions(job.roleName)
}, { immediate: true })
watch(resume, () => {
  if (validationActive.value) fieldErrors.value = toValidationErrorMap(validateResume(resume.value))
}, { deep: true })

const flushLocalCheckpoint = () => localCheckpoint.flush()
onHide(flushLocalCheckpoint)
onBeforeUnmount(flushLocalCheckpoint)

function addEducation() {
  resume.value.education.push({ school: "", major: "", degree: "", startDate: "", endDate: "", courses: "" })
  store.checkpoint()
}

function addEmployment() {
  resume.value.employment.push({ company: "", position: "", startDate: "", endDate: "", description: "" })
  store.checkpoint()
}

function addProject() {
  resume.value.projects.push({ name: "", role: "", startDate: "", endDate: "", description: "" })
  store.checkpoint()
}

function addSuggestedProject() {
  if (!activeJob.value) return
  resume.value.projects.push(createRoleBasedProjectDraft(activeJob.value))
  store.checkpoint()
  uni.showToast({ title: "已添加项目草案，请补全真实信息", icon: "none" })
}

function addSuggestedInternship() {
  if (!activeJob.value) return
  resume.value.employment.push(createRoleBasedInternshipDraft(activeJob.value))
  store.checkpoint()
  uni.showToast({ title: "已添加实习草案，请替换待确认信息", icon: "none" })
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
  if (!store.applyEvidenceSuggestion(suggestion)) {
    uni.showToast({ title: "已有对应经历，不会覆盖", icon: "none" })
    return
  }
  uni.showToast({ title: "已写入空白经历，请补充待确认信息", icon: "success" })
}

async function save() {
  if (saving.value) return
  localCheckpoint.flush()
  validationActive.value = true
  const errors = validateResume(resume.value)
  fieldErrors.value = toValidationErrorMap(errors)
  if (errors.length) return
  saving.value = true
  try {
    const saved = await saveDraft(getClientId(), store.draft)
    checkpointPaused = true
    try {
      store.draft.id = saved.id
      await nextTick()
    } finally {
      checkpointPaused = false
    }
    localCheckpoint.cancel()
    persistLocalCheckpoint()
    uni.showToast({ title: "草稿已保存", icon: "success" })
  } catch {
    localCheckpoint.cancel()
    persistLocalCheckpoint()
    uni.showToast({ title: "网络异常，已保留本地草稿", icon: "none" })
  } finally {
    saving.value = false
  }
}

function prepareAndChooseTemplate() {
  const job = activeJob.value
  if (!job) {
    uni.showToast({ title: "请先查询并选择目标岗位", icon: "none" })
    return
  }
  prepareResumeForJob(store.draft, job)
  store.checkpoint()
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
      <button class="primary" @click="prepareAndChooseTemplate">智能补全并选择模板</button>
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
.primary { color: #fff; background: #1677ff; }.secondary { color: #4e5969; background: #f2f3f5; }
.enrichment-card { background: #f7faff; border-color: #b7d8ff; }
.enrichment-hint { display: block; margin-top: 14rpx; color: #4e5969; line-height: 1.6; }
.enrichment-actions { display: flex; gap: 16rpx; margin-top: 20rpx; }.enrichment-actions button { flex: 1; font-size: 24rpx; }
.evidence-entry { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; margin-top: 22rpx; padding: 18rpx; background: #eef6ff; border: 1rpx solid #cfe4ff; border-radius: 14rpx; }
.evidence-entry-title, .evidence-entry-hint { display: block; }.evidence-entry-title { color: #245b99; font-size: 25rpx; font-weight: 700; }.evidence-entry-hint { margin-top: 5rpx; color: #66788b; font-size: 21rpx; }.evidence-entry button { flex-shrink: 0; }
.suggestion-list { margin-top: 16rpx; }.suggestion-card { margin-top: 12rpx; padding: 16rpx; background: #fff; border: 1rpx solid #d8e8f8; border-radius: 12rpx; }
.suggestion-top { display: flex; align-items: center; justify-content: space-between; gap: 12rpx; color: #245b99; font-size: 24rpx; font-weight: 700; }.suggestion-top text:last-child { color: #86909c; font-size: 20rpx; font-weight: 400; }
.suggestion-description, .suggestion-risk { display: block; margin-top: 10rpx; color: #4e5969; font-size: 22rpx; line-height: 1.55; white-space: pre-line; }.suggestion-risk { color: #b26a00; }.suggestion-card button { margin-top: 12rpx; }
.validation-summary { margin-bottom: 20rpx; padding: 16rpx 20rpx; color: #b42318; background: #fff7f0; border: 1rpx solid #ffccc7; border-radius: 12rpx; }.validation-summary text { display: block; font-size: 23rpx; line-height: 1.55; }
.local-save-status { display: block; min-height: 34rpx; margin-bottom: 12rpx; color: #66788b; font-size: 22rpx; text-align: right; }
</style>
