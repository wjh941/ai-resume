<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { Plus, Save, X } from "lucide-vue-next"

import AsyncButton from "../components/AsyncButton.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import { getDraft, saveDraft, type DraftRecord } from "../lib/drafts"
import { toDraftSaveInput } from "../lib/draft-workflow"

const props = defineProps<{ draftId: string }>()
const emit = defineEmits<{
  cancel: []
  saved: [draft: DraftRecord]
}>()

const draft = ref<DraftRecord | null>(null)
const loading = ref(true)
const saving = ref(false)
const error = ref("")

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
    draft.value = JSON.parse(JSON.stringify(loaded)) as DraftRecord
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
  if (!draft.value || saving.value) return
  saving.value = true
  error.value = ""
  try {
    const saved = await saveDraft(toDraftSaveInput(draft.value))
    draft.value = saved
    emit("saved", saved)
  } catch {
    error.value = "简历草稿暂未保存，请检查登录状态后重试"
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="view-layout resume-editor-view">
    <div class="view-heading">
      <div>
        <h1 id="resume-editor-title">编辑简历草稿</h1>
        <p>补充真实经历与目标岗位信息，保存后可继续完善。</p>
      </div>
      <div class="heading-actions">
        <AsyncButton class="text-action" type="button" @click="emit('cancel')"><X :size="16" aria-hidden="true" />返回草稿</AsyncButton>
        <AsyncButton class="primary-button compact" type="button" :loading="saving" :disabled="loading" @click="save"><Save :size="16" aria-hidden="true" />保存草稿</AsyncButton>
      </div>
    </div>

    <div v-if="loading" class="content-skeleton editor-loading" aria-busy="true">
      <LoadingSpinner class="content-loading-spinner" label="正在读取简历草稿" />
      <span /><span /><span /><span />
    </div>
    <p v-else-if="error && !draft" class="notice-error" role="alert">{{ error }}</p>
    <form v-else-if="draft" class="resume-editor-form" @submit.prevent="save">
      <p v-if="error" class="notice-error" role="alert">{{ error }}</p>
      <section class="editor-section">
        <h2>基本信息</h2>
        <div class="editor-grid">
          <label><span>草稿名称</span><input v-model.trim="draft.jobTitle" maxlength="160" required /></label>
          <label><span>简历模板</span><select v-model="draft.templateId"><option value="business">商务模板</option><option value="technology">技术模板</option><option value="graduate">毕业生模板</option><option value="analytics">分析模板</option></select></label>
          <label><span>姓名</span><input v-model.trim="draft.resume.basic.name" maxlength="80" /></label>
          <label><span>手机号</span><input v-model.trim="draft.resume.basic.phone" maxlength="30" /></label>
          <label><span>邮箱</span><input v-model.trim="draft.resume.basic.email" type="email" maxlength="160" /></label>
          <label><span>城市</span><input v-model.trim="draft.resume.basic.city" maxlength="80" /></label>
          <label><span>目标岗位</span><input v-model.trim="draft.resume.job.targetRole" maxlength="120" /></label>
          <label><span>期望薪资</span><input v-model.trim="draft.resume.job.expectedSalary" maxlength="80" /></label>
          <label><span>工作形式</span><input v-model.trim="draft.resume.job.employmentType" maxlength="80" /></label>
        </div>
      </section>

      <section class="editor-section">
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

      <section class="editor-section">
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

      <section class="editor-section">
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

      <section class="editor-section">
        <h2>技能与自我评价</h2>
        <label><span>技能（用逗号分隔）</span><input v-model="skillsText" /></label>
        <label><span>证书（用逗号分隔）</span><input :value="draft.resume.skills.certificates.join(', ')" @input="updateCertificates" /></label>
        <label><span>自我评价</span><textarea v-model.trim="draft.resume.selfEvaluation" rows="5" /></label>
      </section>

      <AsyncButton class="primary-button" type="submit" :loading="saving"><Save :size="17" aria-hidden="true" />保存草稿</AsyncButton>
    </form>
  </section>
</template>
