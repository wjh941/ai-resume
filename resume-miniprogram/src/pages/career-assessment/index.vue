<script setup lang="ts">
import { computed, onMounted, ref } from "vue"

import {
  getAssessmentQuestions,
  listAnnualInsights,
  submitAssessment,
} from "../../services/assessment-api"
import { getClientId } from "../../stores/session"
import { useAssessmentStore } from "../../stores/assessment"
import type { AssessmentQuestionGroup } from "../../types/assessment"

const store = useAssessmentStore()
const currentStep = ref(0)
const loading = ref(false)
const submitting = ref(false)
const error = ref("")

const steps: Array<{ group: AssessmentQuestionGroup; title: string; hint: string }> = [
  { group: "interest", title: "兴趣偏好", hint: "更愿意投入哪类任务" },
  { group: "work_style", title: "工作方式", hint: "你偏好的协作与处理方式" },
  { group: "strength_evidence", title: "专长证据", hint: "只记录能举出真实例子的能力" },
  { group: "constraints", title: "现实约束", hint: "用于安排可执行的求职节奏" },
]

const scaleOptions = [
  { value: 1, label: "完全不符合" },
  { value: 2, label: "不太符合" },
  { value: 3, label: "不确定" },
  { value: 4, label: "比较符合" },
  { value: 5, label: "非常符合" },
]

const currentGroup = computed(() => steps[currentStep.value]?.group ?? "interest")
const currentQuestions = computed(() =>
  store.questions.filter((question) => question.group === currentGroup.value),
)
const result = computed(() => store.result?.result ?? null)

function answer(key: string, value: number) {
  store.answer(key, value)
}

function goNext() {
  if (currentStep.value < steps.length - 1) currentStep.value += 1
  else void submit()
}

function goPrevious() {
  if (currentStep.value > 0) currentStep.value -= 1
}

async function submit() {
  submitting.value = true
  error.value = ""
  try {
    const saved = await submitAssessment(getClientId(), store.answers)
    store.setResult(saved)
    uni.pageScrollTo({ scrollTop: 0, duration: 250 })
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "测评结果保存失败，请检查后端服务。"
  } finally {
    submitting.value = false
  }
}

async function initialize() {
  loading.value = true
  error.value = ""
  try {
    const [questions, insights] = await Promise.all([
      getAssessmentQuestions(),
      listAnnualInsights(),
    ])
    store.setQuestions(questions.items, questions.notice)
    store.setInsights(insights)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "测评加载失败，请检查后端服务。"
  } finally {
    loading.value = false
  }
}

function openPlanner() {
  uni.navigateTo({ url: "/pages/career-planner/index" })
}

onMounted(() => {
  void initialize()
})
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="content">
      <view class="hero">
        <text class="eyebrow">GRADUATE CAREER ASSESSMENT</text>
        <text class="title">职业偏好与专长测评</text>
        <text class="subtitle">用真实证据和现实约束，生成更可执行的求职方向建议。</text>
      </view>

      <view class="notice-card">
        <text class="notice-title">使用边界</text>
        <text class="notice-text">{{ store.notice || "本测评用于职业决策支持，不是心理或医疗诊断，也不承诺就业结果。" }}</text>
      </view>

      <view v-if="loading" class="card loading-card"><text>正在加载测评题目…</text></view>
      <text v-if="error" class="error">{{ error }}</text>

      <template v-if="!loading && !result">
        <view class="stepper">
          <view
            v-for="(step, index) in steps"
            :key="step.group"
            class="step"
            :class="{ active: index === currentStep, done: index < currentStep }"
          >
            <text>{{ index + 1 }}</text><text>{{ step.title }}</text>
          </view>
        </view>

        <view class="card">
          <text class="section-title">{{ steps[currentStep].title }}</text>
          <text class="section-hint">{{ steps[currentStep].hint }}。每道题可跳过，未作答不会被视为你的优势。</text>
          <view v-for="question in currentQuestions" :key="question.key" class="question">
            <text class="question-title">{{ question.title }}</text>
            <view class="scale-row">
              <button
                v-for="option in scaleOptions"
                :key="option.value"
                class="scale-button"
                :class="{ selected: store.answers[question.key] === option.value }"
                @click="answer(question.key, option.value)"
              >{{ option.value }}</button>
            </view>
            <text v-if="store.answers[question.key]" class="selected-label">
              {{ scaleOptions.find((item) => item.value === store.answers[question.key])?.label }}
            </text>
          </view>

          <view class="button-row">
            <button class="secondary" :disabled="currentStep === 0" @click="goPrevious">上一步</button>
            <button class="primary" :loading="submitting" @click="goNext">
              {{ currentStep === steps.length - 1 ? "生成测评建议" : "下一步" }}
            </button>
          </view>
        </view>
      </template>

      <template v-else-if="result">
        <view class="card result-card">
          <text class="section-title">你的当前职业信号</text>
          <text class="summary">{{ result.workStyleSummary }}</text>
          <text class="confidence">{{ result.confidenceNote }}</text>
          <view class="chip-row">
            <text v-for="item in result.topInterests" :key="item.key" class="chip">
              {{ item.label }} · {{ item.score }}
            </text>
          </view>
          <text v-if="!result.topInterests.length" class="hint">尚未形成明确的高偏好方向，建议补充作答或结合真实项目复盘。</text>
        </view>

        <view class="card">
          <text class="section-title">已说明的真实证据</text>
          <text v-if="!result.strengthEvidence.length" class="hint">暂未记录足够的优势证据。请优先整理真实课程、项目或实习经历。</text>
          <text v-for="item in result.strengthEvidence" :key="item" class="bullet">- {{ item }}</text>
        </view>

        <view class="card">
          <text class="section-title">7 / 30 / 90 天行动计划</text>
          <view class="plan-section"><text>7 天内</text><text v-for="item in result.actionPlan.sevenDay" :key="item" class="bullet">- {{ item }}</text></view>
          <view class="plan-section"><text>30 天内</text><text v-for="item in result.actionPlan.thirtyDay" :key="item" class="bullet">- {{ item }}</text></view>
          <view class="plan-section"><text>90 天内</text><text v-for="item in result.actionPlan.ninetyDay" :key="item" class="bullet">- {{ item }}</text></view>
          <button class="primary" @click="openPlanner">结合专业生成职业规划</button>
        </view>
      </template>

      <view v-if="store.insights.length" class="card insight-card">
        <text class="section-title">年度就业洞察</text>
        <view v-for="item in store.insights" :key="item.id" class="insight">
          <text class="insight-title">{{ item.year }} · {{ item.title }}</text>
          <text class="insight-text">{{ item.content }}</text>
          <text class="insight-source">来源：{{ item.sourceLabel }} · {{ item.publicationDate }}</text>
          <text class="insight-source">{{ item.confidenceNote }}</text>
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; background: #f4f7fb; color: #1f2937; }
.content { padding: 24rpx 24rpx 58rpx; }
.hero { padding: 34rpx 24rpx 30rpx; background: linear-gradient(145deg, #e7f1ff, #f7fbff); border-radius: 24rpx; }
.eyebrow { display: block; color: #1677ff; font-size: 21rpx; font-weight: 700; letter-spacing: 1rpx; }
.title { display: block; margin-top: 10rpx; font-size: 44rpx; font-weight: 700; }
.subtitle,.notice-text,.section-hint,.summary,.confidence,.hint,.insight-text,.insight-source { display: block; margin-top: 12rpx; color: #64748b; font-size: 24rpx; line-height: 1.6; }
.notice-card,.card { margin-top: 20rpx; padding: 24rpx; background: #fff; border: 1rpx solid #e2e8f0; border-radius: 20rpx; box-shadow: 0 10rpx 28rpx rgba(35, 78, 130, .06); }
.notice-card { background: #fff9ee; border-color: #f6dfb7; }
.notice-title,.section-title { display: block; color: #1f2937; font-size: 30rpx; font-weight: 700; }
.notice-text { color: #7c633c; }
.error { display: block; margin: 18rpx 4rpx; color: #d4380d; font-size: 24rpx; }
.loading-card { color: #64748b; font-size: 25rpx; }
.stepper { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10rpx; margin-top: 20rpx; }
.step { padding: 14rpx 8rpx; color: #8a97a8; background: #edf2f7; border-radius: 14rpx; text-align: center; }
.step text { display: block; font-size: 20rpx; }.step text:first-child { font-size: 26rpx; font-weight: 700; }.step.active,.step.done { color: #fff; background: #1677ff; }
.question { margin-top: 26rpx; padding-bottom: 22rpx; border-bottom: 1rpx solid #eef2f7; }
.question:last-child { border-bottom: 0; padding-bottom: 0; }.question-title { display: block; color: #334155; font-size: 27rpx; font-weight: 600; line-height: 1.55; }
.scale-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10rpx; margin-top: 16rpx; }.scale-button { margin: 0; padding: 14rpx 0; color: #5c6b7d; background: #f2f5f8; border: 1rpx solid #e1e7ee; border-radius: 12rpx; font-size: 24rpx; }.scale-button.selected { color: #fff; background: #1677ff; border-color: #1677ff; }
.selected-label { display: block; margin-top: 10rpx; color: #1677ff; font-size: 22rpx; }.button-row { display: flex; gap: 14rpx; margin-top: 28rpx; }.button-row button { flex: 1; border-radius: 12rpx; font-size: 26rpx; }.primary { margin-top: 20rpx; color: #fff; background: #1677ff; border-radius: 12rpx; font-size: 27rpx; }.button-row .primary { margin-top: 0; }.secondary { color: #53667b; background: #edf2f7; }
.chip-row { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 16rpx; }.chip { padding: 8rpx 14rpx; color: #1677ff; background: #e8f3ff; border-radius: 999rpx; font-size: 23rpx; }.bullet { display: block; margin-top: 12rpx; color: #475569; font-size: 24rpx; line-height: 1.6; }.plan-section { margin-top: 20rpx; padding: 16rpx; background: #f8fafc; border-radius: 14rpx; }.plan-section > text:first-child { display: block; color: #1d4e89; font-size: 26rpx; font-weight: 700; }
.insight { margin-top: 18rpx; padding-top: 18rpx; border-top: 1rpx solid #eef2f7; }.insight:first-of-type { border-top: 0; padding-top: 0; }.insight-title { display: block; color: #334155; font-size: 26rpx; font-weight: 700; }.insight-source { color: #86909c; font-size: 21rpx; }
@media (max-width: 360px) { .content { padding-right: 18rpx; padding-left: 18rpx; }.step { padding-right: 4rpx; padding-left: 4rpx; }.step text:last-child { font-size: 18rpx; } }
</style>
