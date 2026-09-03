<script setup lang="ts">
import { ClipboardList, RefreshCw, Send, Sparkles } from "lucide-vue-next"
import { computed, onMounted, ref, watch } from "vue"

import AsyncButton from "../components/AsyncButton.vue"
import AssessmentQuestionCard from "../components/AssessmentQuestionCard.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import { getAssessmentQuestions, loadAssessment, submitAssessment, type AssessmentQuestion, type AssessmentReport } from "../lib/assessment"
import {
  ASSESSMENT_INCOMPLETE_ERROR,
  clearAssessmentValidationError,
  flattenActionPlan,
  isAssessmentComplete,
  mergeAssessmentAnswers,
  resolveAssessmentSubmitAction,
} from "../lib/assessment-workflow"
import type { WorkspaceView } from "../components/WebSidebar.vue"
import { readSession } from "../lib/session"
import { clearWorkspaceSnapshot, readWorkspaceSnapshot, writeWorkspaceSnapshot } from "../lib/workspace-recovery"

const emit = defineEmits<{ navigate: [view: WorkspaceView] }>()
const questions = ref<AssessmentQuestion[]>([])
const notice = ref("")
const answers = ref<Record<string, number>>({})
const result = ref<AssessmentReport | null>(null)
const loading = ref(true)
const saving = ref(false)
const error = ref("")
const validationActive = ref(false)
const reportMode = ref<"simplified" | "professional">("simplified")
const workspaceUserId = readSession()?.user.user_id ?? ""
const workspaceStorage = typeof sessionStorage === "undefined" ? null : sessionStorage
const answeredCount = computed(() => Object.keys(answers.value).length)
const complete = computed(() => isAssessmentComplete(questions.value, answers.value))

watch(complete, (value) => {
  if (!value) return
  validationActive.value = false
  error.value = clearAssessmentValidationError(value, error.value)
})

watch(answers, (value) => {
  if (workspaceStorage) writeWorkspaceSnapshot(workspaceStorage, workspaceUserId, "assessment", value)
}, { deep: true })

async function refresh(): Promise<void> {
  loading.value = true; error.value = ""; notice.value = ""
  const [questionResponse, savedResponse] = await Promise.allSettled([getAssessmentQuestions(), loadAssessment()])
  if (questionResponse.status === "fulfilled") { questions.value = questionResponse.value.items; notice.value = questionResponse.value.notice }
  else { error.value = "暂时无法读取测评题目，请稍后重试" }
  const recovered = workspaceStorage ? readWorkspaceSnapshot<Record<string, number>>(workspaceStorage, workspaceUserId, "assessment") : null
  if (savedResponse.status === "fulfilled") {
    answers.value = mergeAssessmentAnswers(mergeAssessmentAnswers(answers.value, savedResponse.value.answers), recovered ?? {})
    result.value = savedResponse.value.result
  } else if (recovered) answers.value = mergeAssessmentAnswers(answers.value, recovered)
  loading.value = false
}
async function submit(): Promise<void> {
  const action = resolveAssessmentSubmitAction(complete.value, saving.value)
  if (action === "show-validation") {
    validationActive.value = true
    error.value = ASSESSMENT_INCOMPLETE_ERROR
    return
  }
  if (action === "ignore") return
  saving.value = true; error.value = ""
  try {
    const saved = await submitAssessment(answers.value, reportMode.value)
    result.value = saved.result
    if (workspaceStorage) clearWorkspaceSnapshot(workspaceStorage, workspaceUserId, "assessment")
  } catch (caught) { error.value = caught instanceof Error ? caught.message : "测评暂未提交，请稍后重试" } finally { saving.value = false }
}
onMounted(refresh)
</script>

<template>
  <section class="view-layout assessment-view">
    <div class="view-heading"><div><h1 id="assessment-title">职业测评</h1><p>用一组结构化问题整理当前偏好与能力线索，结果用于职业决策支持，不是心理或医疗诊断。</p></div><AsyncButton class="text-action" type="button" :loading="loading" @click="refresh"><RefreshCw :size="16" aria-hidden="true" />刷新</AsyncButton></div>
    <ErrorNotice v-if="error" :message="error" /><p v-if="notice" class="source-notice">{{ notice }}</p>
    <div v-if="loading" class="content-skeleton assessment-loading" aria-busy="true"><LoadingSpinner class="content-loading-spinner" label="正在读取测评题目" /><span /><span /><span /></div>
    <template v-else>
      <section class="assessment-panel decision-surface"><div class="panel-heading"><div><span class="section-kicker"><ClipboardList :size="14" aria-hidden="true" />答题进度</span><h2>完成 {{ answeredCount }} / {{ questions.length }}</h2></div><div class="mode-switch" aria-label="报告模式"><button type="button" :disabled="saving" :class="{ 'is-selected': reportMode === 'simplified' }" @click="reportMode = 'simplified'">简版结果</button><button type="button" :disabled="saving" :class="{ 'is-selected': reportMode === 'professional' }" @click="reportMode = 'professional'">专业版</button></div></div><div class="assessment-question-grid"><AssessmentQuestionCard v-for="question in questions" :key="question.key" :question="question" :model-value="answers[question.key]" :disabled="saving" :invalid="validationActive && !Number.isInteger(answers[question.key])" @update:model-value="answers[question.key] = $event" /></div><AsyncButton class="primary-button" type="button" :loading="saving" :disabled="saving" @click="submit"><Send :size="17" aria-hidden="true" />提交测评</AsyncButton></section>
      <section v-if="result" class="assessment-result decision-surface decision-emphasis"><div class="result-heading"><div><span class="section-kicker"><Sparkles :size="14" aria-hidden="true" />测评结果</span><h2>{{ result.workStyleSummary || "你的结果已生成" }}</h2><p v-if="result.confidenceNote">{{ result.confidenceNote }}</p></div><span class="report-mode-label">{{ result.reportScope || reportMode }}</span></div><div v-if="result.upgradeNotice" class="notice-with-action report-actions"><p>{{ result.upgradeNotice }}</p><AsyncButton class="notice-action" type="button" @click="emit('navigate', 'membership')">查看会员权益</AsyncButton></div><div v-if="result.topInterests.length" class="assessment-result-grid"><section><h3>兴趣方向</h3><ul class="tag-list"><li v-for="item in result.topInterests" :key="item.key">{{ item.label }} · {{ item.score }}</li></ul></section><section><h3>优势线索</h3><ul class="plain-list"><li v-for="item in result.strengthEvidence" :key="item">{{ item }}</li></ul></section><section><h3>行动计划</h3><ol class="plain-list"><li v-for="item in flattenActionPlan(result)" :key="item">{{ item }}</li></ol></section></div></section>
      <div v-else class="empty-board"><Sparkles :size="28" aria-hidden="true" /><div><h2>完成答题后查看结果</h2><p>答案会保留在当前页面，提交失败时不会清空。</p></div></div>
    </template>
  </section>
</template>
