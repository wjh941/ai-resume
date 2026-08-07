<script setup lang="ts">
import { computed, ref } from "vue"

import {
  extractResumePdf,
  queryCareerAdvice,
  queryJobConsultation,
  reviewResumeText,
} from "../../services/resume-api"
import { IDENTITY_OPTIONS, IDENTITY_PROMPT, useConsultationStore } from "../../stores/consultation"
import { useResumeStore } from "../../stores/resume"
import type { AdviceTopic, CareerAdvice, JobConsultation, ResumeReview } from "../../types/consultation"
import { prepareResumeForJob } from "../../utils/resume-autofill"

const roleName = ref("")
const resumeText = ref("")
const customRequirement = ref("")
const adviceQuestion = ref("")
const selectedAdviceIndex = ref(0)
const loading = ref(false)
const reviewLoading = ref(false)
const adviceLoading = ref(false)
const pdfLoading = ref(false)
const error = ref("")
const reviewError = ref("")
const adviceError = ref("")
const jobConsultation = ref<JobConsultation | null>(null)
const resumeReview = ref<ResumeReview | null>(null)
const careerAdvice = ref<CareerAdvice | null>(null)
const store = useResumeStore()
const consultation = useConsultationStore()
const identityPromptLines = IDENTITY_PROMPT.split("\n")
const canReviewResume = computed(() => consultation.identityCode !== null)
const adviceTopics: Array<{ topic: AdviceTopic; label: string }> = [
  { topic: "simulation_interview", label: "模拟面试" },
  { topic: "salary_negotiation", label: "薪资谈判" },
  { topic: "contract_pitfalls", label: "合同避坑" },
  { topic: "career_planning", label: "职业规划" },
  { topic: "certificate_recommendation", label: "证书推荐" },
  { topic: "role_comparison", label: "岗位对比" },
  { topic: "written_test", label: "笔试准备" },
  { topic: "job_channels", label: "招聘渠道" },
  { topic: "scam_screening", label: "求职避坑" },
]
const selectedAdviceTopic = computed(() => adviceTopics[selectedAdviceIndex.value] ?? adviceTopics[0])

function resetResults() {
  jobConsultation.value = null
  resumeReview.value = null
  careerAdvice.value = null
  reviewError.value = ""
  adviceError.value = ""
}

async function beginConsultation() {
  const role = roleName.value.trim()
  if (!role) {
    error.value = "请输入岗位名称"
    return
  }
  error.value = ""
  resetResults()
  const nextStep = consultation.beginRoleConsultation(role)
  if (nextStep === "identity-selection") return
  await loadJobAnalysis(consultation.identityCode!)
}

function changeIdentity() {
  resetResults()
  consultation.beginIdentitySelection(consultation.pendingRoleName || roleName.value)
}

async function selectIdentity(identityCode: (typeof IDENTITY_OPTIONS)[number]["code"]) {
  consultation.selectIdentity(identityCode)
  await loadJobAnalysis(identityCode)
}

async function loadJobAnalysis(identityCode: (typeof IDENTITY_OPTIONS)[number]["code"]) {
  loading.value = true
  error.value = ""
  try {
    const result = await queryJobConsultation(
      consultation.pendingRoleName,
      identityCode,
      customRequirement.value.trim(),
    )
    jobConsultation.value = result
    store.setJobIntelligence(result.jobIntelligence)
    consultation.showJobAnalysis()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "岗位解析失败"
  } finally {
    loading.value = false
  }
}

function startResume() {
  if (!jobConsultation.value) return
  prepareResumeForJob(store.draft, jobConsultation.value.jobIntelligence)
  store.checkpoint()
  uni.navigateTo({ url: "/pages/template-picker/index" })
}

async function reviewResume() {
  const text = resumeText.value.trim()
  if (!text) {
    reviewError.value = "请粘贴需要优化的简历内容，或先上传 PDF"
    return
  }
  if (!consultation.identityCode) {
    reviewError.value = "请先选择求职身份"
    return
  }
  reviewLoading.value = true
  reviewError.value = ""
  resumeReview.value = null
  try {
    resumeReview.value = await reviewResumeText(
      text,
      consultation.identityCode,
      jobConsultation.value?.jobIntelligence.roleName || consultation.pendingRoleName,
      customRequirement.value.trim(),
    )
  } catch (reason) {
    reviewError.value = reason instanceof Error ? reason.message : "简历优化失败"
  } finally {
    reviewLoading.value = false
  }
}

type FileChoice = { tempFiles?: Array<{ path?: string }> }
type ChooseFile = (options: {
  count: number
  type: "file"
  extension: string[]
  success: (result: FileChoice) => void
  fail: (reason: unknown) => void
}) => void

function chooseResumePdf() {
  const chooseFile = (globalThis as typeof globalThis & { uni?: { chooseFile?: ChooseFile } }).uni?.chooseFile
  if (!chooseFile) {
    reviewError.value = "当前运行环境不支持 PDF 文件选择，请直接粘贴简历文本"
    return
  }
  chooseFile({
    count: 1,
    type: "file",
    extension: ["pdf"],
    success: async (result) => {
      const filePath = result.tempFiles?.[0]?.path
      if (!filePath) {
        reviewError.value = "未读取到 PDF 文件"
        return
      }
      pdfLoading.value = true
      reviewError.value = ""
      try {
        resumeText.value = await extractResumePdf(filePath)
      } catch (reason) {
        reviewError.value = reason instanceof Error ? reason.message : "PDF 文本提取失败"
      } finally {
        pdfLoading.value = false
      }
    },
    fail: () => {
      reviewError.value = "未选择 PDF 文件"
    },
  })
}

function selectAdviceTopic(event: Event) {
  const value = (event as unknown as { detail?: { value?: string } }).detail?.value
  const index = Number(value)
  if (Number.isInteger(index) && index >= 0 && index < adviceTopics.length) {
    selectedAdviceIndex.value = index
  }
}

async function requestCareerAdvice() {
  if (!consultation.identityCode) {
    adviceError.value = "请先选择求职身份"
    return
  }
  adviceLoading.value = true
  adviceError.value = ""
  careerAdvice.value = null
  try {
    careerAdvice.value = await queryCareerAdvice(
      consultation.identityCode,
      selectedAdviceTopic.value.topic,
      jobConsultation.value?.jobIntelligence.roleName || consultation.pendingRoleName,
      adviceQuestion.value.trim(),
    )
  } catch (reason) {
    adviceError.value = reason instanceof Error ? reason.message : "求职建议生成失败"
  } finally {
    adviceLoading.value = false
  }
}

function isRiskItem(item: string) {
  return item.includes("【避雷】") || item.includes("【高频坑】")
}
</script>

<template>
  <view class="page">
    <view class="hero">
      <text class="title">AI 求职顾问</text>
      <text class="subtitle">岗位解析、简历批改与求职工具，按你的身份给出可执行方案</text>
    </view>

    <view class="search-card">
      <input v-model="roleName" placeholder="例如：数据工程师" confirm-type="search" @confirm="beginConsultation" />
      <textarea
        v-model="customRequirement"
        class="custom-requirement-input"
        placeholder="可选：补充你的岗位偏好或特殊需求，例如目标城市、双休、行业方向"
        auto-height
      />
      <button class="primary" :loading="loading" @click="beginConsultation">查询岗位情报</button>
      <text v-if="error" class="error">{{ error }}</text>
    </view>

    <view v-if="consultation.stage === 'identity-selection'" class="identity-card">
      <text v-for="line in identityPromptLines" :key="line" class="identity-prompt">{{ line }}</text>
      <view class="identity-options">
        <button
          v-for="option in IDENTITY_OPTIONS"
          :key="option.code"
          class="identity-button"
          :loading="loading"
          :disabled="loading"
          @click="selectIdentity(option.code)"
        >
          {{ option.code }} {{ option.label }}
        </button>
      </view>
    </view>

    <view v-if="jobConsultation" class="result">
      <view class="result-header">
        <view>
          <text class="role">{{ jobConsultation.jobIntelligence.roleName }}</text>
          <text class="identity-name">当前身份：{{ jobConsultation.identityLabel }}</text>
        </view>
        <button class="secondary compact" @click="changeIdentity">切换身份</button>
      </view>
      <text class="notice">{{ jobConsultation.marketNotice }}</text>
      <view v-if="jobConsultation.customRequirementNotes.length" class="custom-note">
        <text class="block-title">## 已纳入你的补充需求</text>
        <text v-for="item in jobConsultation.customRequirementNotes" :key="item" class="list-item">- {{ item }}</text>
      </view>
      <text class="result-title">## 岗位深度全解析</text>
      <view v-for="section in jobConsultation.jobAnalysisSections" :key="section.order" class="block">
        <text class="block-title">## {{ section.order }}. {{ section.title }}</text>
        <text
          v-for="item in section.items"
          :key="item"
          :class="['list-item', { 'risk-item': isRiskItem(item) }]"
        >- {{ item }}</text>
      </view>

      <text class="result-title">## 职业晋升路线</text>
      <view
        v-for="stage in jobConsultation.careerGrowthRoute.stages"
        :key="stage.stage"
        class="growth-stage"
      >
        <text class="block-title">{{ stage.stage }}｜{{ stage.roleName }}</text>
        <text class="growth-meta">{{ stage.yearsReference }}</text>
        <text class="list-item">- 核心技能：{{ stage.coreSkills.join(" / ") }}</text>
        <text v-for="item in stage.responsibilities" :key="item" class="list-item">- 工作职责：{{ item }}</text>
        <text v-for="item in stage.assessmentCriteria" :key="item" class="list-item">- 考核标准：{{ item }}</text>
      </view>

      <text class="result-title">## 对应人群全套求职解决方案</text>
      <text class="identity-name">{{ jobConsultation.identityPlan.title }}</text>
      <view v-for="section in jobConsultation.identityPlan.sections" :key="section.order" class="block plan-block">
        <text class="block-title">## {{ section.title }}</text>
        <text v-for="item in section.items" :key="item" class="list-item">- {{ item }}</text>
      </view>
      <text class="follow-up">{{ jobConsultation.followUpQuestion }}</text>
      <button class="primary" @click="startResume">以此岗位生成简历</button>
    </view>

    <view v-if="canReviewResume" class="review-card">
      <text class="review-title">简历专项批改</text>
      <text class="review-hint">粘贴简历文本或上传 PDF 提取文字后，生成问题标注、替换范文、完整草稿和面试自我介绍。</text>
      <textarea
        v-model="resumeText"
        class="resume-textarea"
        placeholder="直接粘贴简历文本。系统会保留真实经历，只将未知信息标为[待确认]。"
        auto-height
      />
      <view class="button-row">
        <button class="secondary" :loading="pdfLoading" @click="chooseResumePdf">上传 PDF 提取文字</button>
        <button class="primary inline-primary" :loading="reviewLoading" @click="reviewResume">批改简历</button>
      </view>
      <text v-if="reviewError" class="error">{{ reviewError }}</text>
    </view>

    <view v-if="resumeReview" class="result review-result">
      <text class="result-title">## 简历问题逐条标注</text>
      <text v-for="item in resumeReview.issues" :key="item" class="list-item">- {{ item }}</text>
      <text class="result-title">## 逐段优化范文</text>
      <text v-for="item in resumeReview.rewriteExamples" :key="item" class="list-item">- {{ item }}</text>
      <text class="result-title">## 加分关键词</text>
      <text class="keywords">{{ resumeReview.keywords.join(" / ") }}</text>
      <text class="result-title">## 可复制完整简历文本</text>
      <text class="copy-text">{{ resumeReview.optimizedResumeText }}</text>
      <text class="result-title">## 1分钟面试自我介绍</text>
      <text class="copy-text">{{ resumeReview.interviewIntro }}</text>
      <view v-if="resumeReview.customRequirementNotes.length" class="custom-note">
        <text class="block-title">## 已纳入你的补充需求</text>
        <text v-for="item in resumeReview.customRequirementNotes" :key="item" class="list-item">- {{ item }}</text>
      </view>
      <text class="result-title">## 人岗匹配分析报告</text>
      <view class="match-score-card">
        <text class="match-score">{{ resumeReview.jobMatchReport.score }}%</text>
        <text class="match-score-label">目标岗位匹配度</text>
      </view>
      <text class="block-title">## 评分口径</text>
      <text v-for="item in resumeReview.jobMatchReport.scoreBasis" :key="item" class="list-item">- {{ item }}</text>
      <text class="block-title">## 现有匹配优势</text>
      <text v-for="item in resumeReview.jobMatchReport.matchingAdvantages" :key="item" class="list-item">- {{ item }}</text>
      <text class="block-title">## 缺失技能清单</text>
      <text v-for="item in resumeReview.jobMatchReport.missingSkills" :key="item" class="list-item">- {{ item }}</text>
      <view v-for="gap in resumeReview.jobMatchReport.priorityGaps" :key="gap.skillName" class="priority-gap">
        <text class="priority-gap-title">【需提升】{{ gap.skillName }}</text>
        <text class="list-item">- 学习方向：{{ gap.learningDirection }}</text>
        <text class="list-item">- 项目练习：{{ gap.projectPractice }}</text>
        <text class="list-item">- 练习任务：{{ gap.practiceTask }}</text>
      </view>
    </view>

    <view v-if="canReviewResume" class="toolkit-card">
      <text class="review-title">求职工具箱</text>
      <picker :range="adviceTopics" range-key="label" @change="selectAdviceTopic">
        <view class="picker-value">{{ selectedAdviceTopic.label }} ▾</view>
      </picker>
      <textarea
        v-model="adviceQuestion"
        class="question-textarea"
        placeholder="可补充具体问题，例如：如何确认公积金基数？"
        auto-height
      />
      <button class="primary" :loading="adviceLoading" @click="requestCareerAdvice">获取针对性建议</button>
      <text v-if="adviceError" class="error">{{ adviceError }}</text>
    </view>

    <view v-if="careerAdvice" class="result">
      <text class="result-title">## {{ careerAdvice.title }}</text>
      <view v-for="section in careerAdvice.sections" :key="section.order" class="block plan-block">
        <text class="block-title">## {{ section.title }}</text>
        <text v-for="item in section.items" :key="item" class="list-item">- {{ item }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { padding: 32rpx; background: #f7f8fa; }
.hero { padding: 24rpx 0 32rpx; }
.title { display: block; font-size: 44rpx; font-weight: 700; color: #1f2329; }
.subtitle { display: block; margin-top: 10rpx; color: #86909c; font-size: 26rpx; line-height: 1.55; }
.search-card,.result,.identity-card,.review-card,.toolkit-card {
  margin-top: 24rpx; padding: 24rpx; background: #fff; border: 1rpx solid #e5e6eb;
  border-radius: 18rpx; box-shadow: 0 8rpx 24rpx rgba(31,35,41,.06);
}
input,.resume-textarea,.question-textarea,.custom-requirement-input,.picker-value {
  width: 100%; box-sizing: border-box; padding: 20rpx; background: #f7f8fa; border-radius: 12rpx;
}
input { height: 80rpx; margin-bottom: 18rpx; }
.resume-textarea { min-height: 180rpx; margin: 20rpx 0; line-height: 1.6; }
.question-textarea { min-height: 120rpx; margin: 20rpx 0; line-height: 1.6; }
.custom-requirement-input { min-height: 96rpx; margin: 4rpx 0 8rpx; line-height: 1.6; }
.primary { margin-top: 12rpx; color: #fff; background: #1677ff; }
.secondary { margin-top: 12rpx; color: #4e5969; background: #f2f3f5; }
.identity-prompt { display: block; margin-bottom: 12rpx; font-weight: 600; color: #1f2329; }
.identity-options { display: flex; flex-direction: column; gap: 14rpx; margin-top: 24rpx; }
.identity-button { margin: 0; text-align: left; color: #1677ff; background: #e8f3ff; border: 1rpx solid #b7d8ff; }
.result-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 20rpx; }
.role,.result-title,.review-title { display: block; font-weight: 700; color: #1f2329; }
.role { font-size: 36rpx; }.result-title { margin-top: 32rpx; font-size: 32rpx; }
.review-title { font-size: 32rpx; }.review-hint,.notice { display: block; margin-top: 14rpx; color: #86909c; line-height: 1.55; }
.notice { padding: 14rpx; background: #fff7e8; border-radius: 10rpx; }
.identity-name { display: block; margin-top: 12rpx; color: #1677ff; font-weight: 600; }
.compact { min-width: 144rpx; margin: 0; font-size: 24rpx; }
.block { display: flex; flex-direction: column; gap: 10rpx; margin: 24rpx 0; color: #4e5969; }
.block-title { color: #1f2329; font-weight: 600; }.list-item { line-height: 1.65; }
.plan-block { padding: 20rpx; background: #f7faff; border-radius: 12rpx; }
.custom-note,.growth-stage,.priority-gap { margin-top: 20rpx; padding: 20rpx; background: #f7faff; border-radius: 12rpx; }
.growth-stage { border-left: 6rpx solid #4096ff; }
.growth-meta { display: block; margin: 10rpx 0; color: #1677ff; font-size: 24rpx; }
.risk-item { padding: 12rpx; color: #ad4e00; background: #fff7e8; border-radius: 10rpx; }
.match-score-card { display: flex; align-items: baseline; gap: 16rpx; margin: 18rpx 0; padding: 20rpx; color: #0958d9; background: #e6f4ff; border-radius: 12rpx; }
.match-score { font-size: 52rpx; font-weight: 700; }.match-score-label { font-size: 26rpx; color: #4e5969; }
.priority-gap { background: #fff7e8; border: 1rpx solid #ffe7ba; }.priority-gap-title { display: block; margin-bottom: 10rpx; color: #d46b08; font-weight: 700; }
.follow-up,.keywords { display: block; margin: 20rpx 0; color: #4e5969; line-height: 1.6; }
.review-result { margin-top: 24rpx; }.error { display: block; margin-top: 12rpx; color: #d03050; }
.button-row { display: flex; gap: 16rpx; }.button-row button { flex: 1; font-size: 24rpx; }
.inline-primary { margin-top: 12rpx; }.copy-text { display: block; white-space: pre-line; margin-top: 16rpx; padding: 20rpx; color: #4e5969; background: #f7f8fa; border-radius: 12rpx; line-height: 1.65; }
.picker-value { margin-top: 18rpx; color: #4e5969; border: 1rpx solid #e5e6eb; }
</style>
