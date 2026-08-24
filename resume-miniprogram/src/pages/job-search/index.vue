<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue"

import ExpandableText from "../../components/ExpandableText.vue"
import OnboardingTour from "../../components/OnboardingTour.vue"
import {
  extractResumePdf,
  queryCareerAdvice,
  queryJobConsultation,
  queryJobMarketSearch,
  queryJobSuggestions,
  reviewResumeText,
} from "../../services/resume-api"
import { IDENTITY_OPTIONS, IDENTITY_PROMPT, useConsultationStore } from "../../stores/consultation"
import { useResumeStore } from "../../stores/resume"
import { getAuthUser } from "../../stores/session"
import type {
  AdviceTopic,
  CareerAdvice,
  JobConsultation,
  JobSuggestion,
  MarketSearchReport,
  ResumeReview,
} from "../../types/consultation"
import { prepareResumeForJob } from "../../utils/resume-autofill"
import { completeOnboarding, hasCompletedOnboarding } from "../../utils/onboarding"

const roleName = ref("")
const selectedRoles = ref<string[]>([])
const suggestions = ref<JobSuggestion[]>([])
const suggestionLoading = ref(false)
const resumeText = ref("")
const customRequirement = ref("")
const adviceQuestion = ref("")
const selectedAdviceIndex = ref(0)
const loading = ref(false)
const reviewLoading = ref(false)
const adviceLoading = ref(false)
const pdfLoading = ref(false)
const marketSearchLoading = ref(false)
const error = ref("")
const reviewError = ref("")
const adviceError = ref("")
const jobConsultations = ref<JobConsultation[]>([])
const activeJobIndex = ref(0)
const resumeReview = ref<ResumeReview | null>(null)
const careerAdvice = ref<CareerAdvice | null>(null)
const marketSearchReport = ref<MarketSearchReport | null>(null)
const showTargetPicker = ref(false)
const expandedAnalysisOrders = ref<number[]>([1, 2, 3])
const showOnboarding = ref(false)

const store = useResumeStore()
const consultation = useConsultationStore()
const identityPromptLines = IDENTITY_PROMPT.split("\n")
const canReviewResume = computed(() => consultation.identityCode !== null)
const jobConsultation = computed(
  () => jobConsultations.value[activeJobIndex.value] ?? null,
)
const activeRoleName = computed(() => jobConsultation.value?.jobIntelligence.roleName ?? "")
const visibleSuggestions = computed(() =>
  suggestions.value.filter((suggestion) => !selectedRoles.value.includes(suggestion.roleName)),
)
const activeSalary = computed(() => {
  const salary = jobConsultation.value?.jobIntelligence.salaryByExperience
  return salary?.["1-3_years"] || salary?.graduate || "按城市与企业类型核实"
})
const activeSkills = computed(() => jobConsultation.value?.jobIntelligence.requiredSkills.slice(0, 3) ?? [])
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

let suggestionRequestId = 0

watch(roleName, (value) => {
  void refreshSuggestions(value)
})

function selectedOrTypedRoles(): string[] {
  if (selectedRoles.value.length) return [...selectedRoles.value]
  const typedRole = roleName.value.trim()
  return typedRole ? [typedRole] : []
}

async function refreshSuggestions(value: string) {
  const query = value.trim()
  const requestId = ++suggestionRequestId
  if (!query) {
    suggestions.value = []
    suggestionLoading.value = false
    return
  }

  suggestionLoading.value = true
  try {
    const items = await queryJobSuggestions(query)
    if (requestId === suggestionRequestId) suggestions.value = items
  } catch {
    if (requestId === suggestionRequestId) suggestions.value = []
  } finally {
    if (requestId === suggestionRequestId) suggestionLoading.value = false
  }
}

function selectSuggestion(suggestion: JobSuggestion) {
  if (selectedRoles.value.includes(suggestion.roleName)) return
  if (selectedRoles.value.length >= 3) {
    error.value = "一次最多对比 3 个岗位，请先移除不需要的岗位。"
    return
  }
  error.value = ""
  selectedRoles.value.push(suggestion.roleName)
  roleName.value = ""
  suggestions.value = []
}

function removeSelectedRole(role: string) {
  selectedRoles.value = selectedRoles.value.filter((item) => item !== role)
  jobConsultations.value = jobConsultations.value.filter(
    (item) => item.jobIntelligence.roleName !== role,
  )
  if (activeJobIndex.value >= jobConsultations.value.length) {
    activeJobIndex.value = Math.max(0, jobConsultations.value.length - 1)
  }
  if (jobConsultation.value) store.setJobIntelligence(jobConsultation.value.jobIntelligence)
}

function resetResults() {
  jobConsultations.value = []
  activeJobIndex.value = 0
  resumeReview.value = null
  careerAdvice.value = null
  marketSearchReport.value = null
  reviewError.value = ""
  adviceError.value = ""
  showTargetPicker.value = false
  expandedAnalysisOrders.value = [1, 2, 3]
}

async function beginConsultation() {
  const roles = selectedOrTypedRoles()
  if (!roles.length) {
    error.value = "请输入岗位名称，或从下方联想岗位中选择。"
    return
  }

  error.value = ""
  resetResults()
  const nextStep = consultation.beginRoleConsultation(roles[0])
  if (nextStep === "identity-selection") return
  await loadJobAnalyses(consultation.identityCode!)
}

function changeIdentity() {
  resetResults()
  consultation.beginIdentitySelection(activeRoleName.value || selectedOrTypedRoles()[0] || "")
}

async function selectIdentity(identityCode: (typeof IDENTITY_OPTIONS)[number]["code"]) {
  consultation.selectIdentity(identityCode)
  await loadJobAnalyses(identityCode)
}

async function loadJobAnalyses(identityCode: (typeof IDENTITY_OPTIONS)[number]["code"]) {
  if (loading.value) return
  const roles = selectedOrTypedRoles()
  const rolesToLoad = roles.length ? roles : [consultation.pendingRoleName].filter(Boolean)
  if (!rolesToLoad.length) return

  loading.value = true
  error.value = ""
  try {
    const results = await Promise.all(
      rolesToLoad.map((role) =>
        queryJobConsultation(role, identityCode, customRequirement.value.trim()),
      ),
    )
    jobConsultations.value = results
    activeJobIndex.value = 0
    store.setJobIntelligence(results[0].jobIntelligence)
    consultation.showJobAnalysis()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "岗位分析失败"
  } finally {
    loading.value = false
  }
}

function selectJobConsultation(index: number) {
  const next = jobConsultations.value[index]
  if (!next) return
  activeJobIndex.value = index
  marketSearchReport.value = null
  showTargetPicker.value = false
  expandedAnalysisOrders.value = [1, 2, 3]
  store.setJobIntelligence(next.jobIntelligence)
}

async function loadMarketSearch() {
  if (marketSearchLoading.value || !activeRoleName.value) return
  marketSearchLoading.value = true
  marketSearchReport.value = null
  try {
    marketSearchReport.value = await queryJobMarketSearch(activeRoleName.value)
  } catch (reason) {
    marketSearchReport.value = {
      enabled: false,
      provider: "unavailable",
      notice: reason instanceof Error ? reason.message : "联网市场搜索暂时不可用。",
      results: [],
    }
  } finally {
    marketSearchLoading.value = false
  }
}

function copySourceUrl(url: string) {
  if (!url) return
  uni.setClipboardData({
    data: url,
    success: () => uni.showToast({ title: "来源链接已复制", icon: "none" }),
  })
}

function toggleAnalysisSection(order: number) {
  if (expandedAnalysisOrders.value.includes(order)) {
    expandedAnalysisOrders.value = expandedAnalysisOrders.value.filter((item) => item !== order)
  } else {
    expandedAnalysisOrders.value = [...expandedAnalysisOrders.value, order]
  }
}

function isAnalysisSectionOpen(order: number) {
  return expandedAnalysisOrders.value.includes(order)
}

function openResumeTargetPicker() {
  showTargetPicker.value = true
}

function generateResumeForRole(index: number) {
  selectJobConsultation(index)
  const selected = jobConsultations.value[index]
  if (!selected) return
  prepareResumeForJob(store.draft, selected.jobIntelligence)
  store.checkpoint()
  uni.navigateTo({ url: "/pages/template-picker/index" })
}

async function reviewResume() {
  if (reviewLoading.value || pdfLoading.value) return
  const text = resumeText.value.trim()
  if (!text) {
    reviewError.value = "请粘贴需要优化的简历内容，或先上传 PDF。"
    return
  }
  if (!consultation.identityCode) {
    reviewError.value = "请先选择求职身份。"
    return
  }
  reviewLoading.value = true
  reviewError.value = ""
  resumeReview.value = null
  try {
    resumeReview.value = await reviewResumeText(
      text,
      consultation.identityCode,
      activeRoleName.value || consultation.pendingRoleName,
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
  if (reviewLoading.value || pdfLoading.value) return
  const chooseFile = (globalThis as typeof globalThis & { uni?: { chooseFile?: ChooseFile } }).uni?.chooseFile
  if (!chooseFile) {
    reviewError.value = "当前运行环境不支持 PDF 文件选择，请直接粘贴简历文本。"
    return
  }
  chooseFile({
    count: 1,
    type: "file",
    extension: ["pdf"],
    success: async (result) => {
      const filePath = result.tempFiles?.[0]?.path
      if (!filePath) {
        reviewError.value = "未读取到 PDF 文件。"
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
      reviewError.value = "未选择 PDF 文件。"
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
  if (adviceLoading.value) return
  if (!consultation.identityCode) {
    adviceError.value = "请先选择求职身份。"
    return
  }
  adviceLoading.value = true
  adviceError.value = ""
  careerAdvice.value = null
  try {
    careerAdvice.value = await queryCareerAdvice(
      consultation.identityCode,
      selectedAdviceTopic.value.topic,
      activeRoleName.value || consultation.pendingRoleName,
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
function openCareerPlanner() {
  uni.navigateTo({ url: '/pages/career-planner/index' })
}

function openCareerAssessment() {
  uni.navigateTo({ url: '/pages/career-assessment/index' })
}

function openKnowledgebase() {
  uni.navigateTo({ url: '/pages/knowledgebase/index' })
}

function openAccount() {
  uni.navigateTo({ url: "/pages/account/index" })
}

function finishOnboarding(): void {
  const user = getAuthUser()
  if (user) completeOnboarding(user.userId)
  showOnboarding.value = false
}

function navigateFromOnboarding(destination: "resume" | "career" | "applications"): void {
  const routes = {
    resume: "/pages/resume-form/index",
    career: "/pages/career-planner/index",
    applications: "/pages/applications/index",
  }
  finishOnboarding()
  uni.navigateTo({ url: routes[destination] })
}

onMounted(() => {
  const user = getAuthUser()
  showOnboarding.value = Boolean(user && !hasCompletedOnboarding(user.userId))
})

</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="page-content">
      <view class="hero">
        <text class="hero-kicker">CAREER WORKSPACE</text>
        <text class="title">AI 求职顾问</text>
        <text class="subtitle">从岗位方向、市场信息到简历草案，按你的求职身份给出可执行方案。</text>
        <view class="hero-actions"><button class="planner-entry" @click="openCareerPlanner">求职志愿规划</button><button class="planner-entry" @click="openCareerAssessment">职业测评</button><button class="planner-entry" @click="openKnowledgebase">岗位知识库</button></view>
      </view>

      <view class="account-entry"><button class="planner-entry" @click="openAccount">Account</button></view>
      <view class="search-card">
        <view class="search-header">
          <view>
            <text class="card-eyebrow">岗位工作台</text>
            <text class="card-title">先选方向，再做针对性准备</text>
          </view>
          <text class="search-count">最多 3 个岗位</text>
        </view>

        <view class="search-shell">
          <input
            v-model="roleName"
            class="role-input"
            placeholder="输入“数据”“工程师”或具体岗位"
            confirm-type="search"
            aria-label="目标岗位"
            @confirm="beginConsultation"
          />
          <text class="search-icon" aria-hidden="true">⌕</text>
          <view v-if="roleName.trim() && (suggestionLoading || visibleSuggestions.length)" class="suggestion-popover">
            <text class="popover-title">{{ suggestionLoading ? "正在匹配岗位…" : "匹配岗位" }}</text>
            <transition-group name="suggestion-list" tag="view" class="suggestion-list">
            <button
              v-for="suggestion in visibleSuggestions"
              :key="suggestion.roleName"
              class="suggestion-button"
              :aria-label="`添加岗位 ${suggestion.roleName}`"
              @click="selectSuggestion(suggestion)"
            >
              <view>
                <text class="suggestion-name">{{ suggestion.roleName }}</text>
                <text class="suggestion-category">{{ suggestion.category }}</text>
              </view>
              <text class="suggestion-add">添加</text>
            </button>
            </transition-group>
          </view>
        </view>

        <view v-if="selectedRoles.length" class="selected-role-area">
          <text class="selected-role-title">已选岗位</text>
          <view class="role-chip-list">
            <button
              v-for="role in selectedRoles"
              :key="role"
              class="role-chip"
              :aria-label="`移除已选岗位 ${role}`"
              @click="removeSelectedRole(role)"
            >{{ role }} ×</button>
          </view>
        </view>

        <textarea
          v-model="customRequirement"
          class="custom-requirement-input"
          placeholder="可选：补充目标城市、公司类型、薪资或行业偏好"
          auto-height
        />
        <button class="primary primary-action" :loading="loading" :disabled="loading" aria-label="查询岗位情报" @click="beginConsultation">查询岗位情报</button>
      <text v-if="error" class="ui-error-tip">{{ error }}</text>
      </view>

      <view v-if="loading" class="result loading-skeleton" aria-live="polite">
        <view class="skeleton-title"></view>
        <view class="skeleton-line"></view>
        <view class="skeleton-line"></view>
        <view class="skeleton-line short"></view>
      </view>

      <view v-if="consultation.stage === 'identity-selection'" class="identity-card">
        <text class="card-eyebrow">身份定位</text>
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
            <text class="identity-code">{{ option.code }}</text>
            <text>{{ option.label }}</text>
            <text class="identity-arrow">›</text>
          </button>
        </view>
      </view>

      <view v-if="jobConsultation" class="result">
        <view v-if="jobConsultations.length > 1" class="role-tab-list">
          <button
            v-for="(item, index) in jobConsultations"
            :key="item.jobIntelligence.roleName"
            :class="['role-tab', { 'role-tab-active': index === activeJobIndex }]"
            @click="selectJobConsultation(index)"
          >{{ item.jobIntelligence.roleName }}</button>
        </view>

        <view class="result-header">
          <view>
            <text class="card-eyebrow">当前岗位</text>
            <ExpandableText class="role" :text="jobConsultation.jobIntelligence.roleName" :lines="1" :expand-at="18" label="当前岗位" />
            <text class="identity-name">{{ jobConsultation.identityLabel }}</text>
          </view>
          <button class="secondary compact" @click="changeIdentity">切换身份</button>
        </view>

        <view class="summary-grid">
          <view class="summary-item">
            <text class="summary-label">1-3 年参考薪资</text>
            <text class="summary-value">{{ activeSalary }}</text>
          </view>
          <view class="summary-item">
            <text class="summary-label">优先技能</text>
            <text class="summary-value summary-skills">{{ activeSkills.join(" · ") || "岗位信息加载中" }}</text>
          </view>
        </view>

        <view class="notice-bar">
          <text class="notice-dot"></text>
          <text class="notice">{{ jobConsultation.marketNotice }}</text>
        </view>

        <view v-if="jobConsultation.customRequirementNotes.length" class="custom-note">
          <text class="block-title">已纳入你的补充需求</text>
          <text v-for="item in jobConsultation.customRequirementNotes" :key="item" class="list-item">- {{ item }}</text>
        </view>

        <view class="market-card">
          <view class="market-card-header">
            <view>
              <text class="block-title">联网市场更新</text>
              <text class="market-caption">主动读取公开网页来源，不替代岗位分析结论</text>
            </view>
            <button class="secondary compact" :loading="marketSearchLoading" :disabled="marketSearchLoading" @click="loadMarketSearch">联网更新</button>
          </view>
          <text v-if="marketSearchReport" :class="['market-notice', { 'market-disabled': !marketSearchReport.enabled }]">
            {{ marketSearchReport.notice }}
          </text>
          <view
            v-for="source in marketSearchReport?.results"
            :key="source.url"
            class="market-source ui-long-list-item"
            role="button"
            tabindex="0"
            :aria-label="`复制来源链接 ${source.title}`"
            @click="copySourceUrl(source.url)"
            @keydown.enter="copySourceUrl(source.url)"
            @keydown.space.prevent="copySourceUrl(source.url)"
          >
            <view>
              <text class="market-source-title">{{ source.title }}</text>
              <text class="market-source-text">{{ source.snippet }}</text>
              <text v-if="source.publishedDate" class="market-source-date">{{ source.publishedDate }}</text>
            </view>
            <text class="source-copy">复制链接</text>
          </view>
        </view>

        <text class="result-title">岗位深度全解析</text>
        <view
          v-for="section in jobConsultation.jobAnalysisSections"
          :key="section.order"
          class="analysis-section ui-long-list-item"
        >
          <view
            class="analysis-section-header"
            role="button"
            tabindex="0"
            :aria-expanded="isAnalysisSectionOpen(section.order)"
            :aria-label="`${section.title}，${isAnalysisSectionOpen(section.order) ? '收起' : '展开'}`"
            @click="toggleAnalysisSection(section.order)"
            @keydown.enter="toggleAnalysisSection(section.order)"
            @keydown.space.prevent="toggleAnalysisSection(section.order)"
          >
            <view>
              <text class="analysis-index">{{ String(section.order).padStart(2, "0") }}</text>
              <text class="block-title">{{ section.title }}</text>
            </view>
            <text class="section-toggle">{{ isAnalysisSectionOpen(section.order) ? "收起" : "展开" }}</text>
          </view>
          <view v-if="isAnalysisSectionOpen(section.order)" class="analysis-section-body">
            <text
              v-for="item in section.items"
              :key="item"
              :class="['list-item', { 'risk-item': isRiskItem(item) }]"
            >- {{ item }}</text>
          </view>
        </view>

        <text class="result-title">职业晋升路线</text>
        <view
          v-for="stage in jobConsultation.careerGrowthRoute.stages"
          :key="stage.stage"
          class="growth-stage ui-long-list-item"
        >
          <text class="growth-stage-title">{{ stage.stage }} · {{ stage.roleName }}</text>
          <text class="growth-meta">{{ stage.yearsReference }}</text>
          <text class="list-item">- 核心技能：{{ stage.coreSkills.join(" / ") }}</text>
          <text v-for="item in stage.responsibilities" :key="item" class="list-item">- 工作职责：{{ item }}</text>
          <text v-for="item in stage.assessmentCriteria" :key="item" class="list-item">- 考核标准：{{ item }}</text>
        </view>

        <text class="result-title">身份适配求职方案</text>
        <text class="identity-plan-title">{{ jobConsultation.identityPlan.title }}</text>
        <view v-for="section in jobConsultation.identityPlan.sections" :key="section.order" class="plan-block ui-long-list-item">
          <text class="block-title">{{ section.title }}</text>
          <text v-for="item in section.items" :key="item" class="list-item">- {{ item }}</text>
        </view>
        <text class="follow-up">{{ jobConsultation.followUpQuestion }}</text>

        <view class="resume-callout">
          <text class="resume-callout-title">按目标岗位生成简历</text>
          <text class="resume-callout-text">空白项目和实习经历会补出 2 个项目草案和 1 个实习草案，所有未知事实均保留 [待确认]。</text>
          <button class="primary primary-action" @click="openResumeTargetPicker">选择岗位并制作简历</button>
        </view>

        <view v-if="showTargetPicker" class="target-picker">
          <text class="target-picker-title">选择本次优化的目标岗位</text>
          <text class="target-picker-hint">将添加岗位关键词与可编辑草案，不会覆盖你已有的真实经历。</text>
          <button
            v-for="(item, index) in jobConsultations"
            :key="item.jobIntelligence.roleName"
            class="target-role-button"
            @click="generateResumeForRole(index)"
          >按“{{ item.jobIntelligence.roleName }}”优化并制作简历</button>
        </view>
      </view>

      <view v-if="canReviewResume" class="review-card">
        <text class="card-eyebrow">简历专项批改</text>
        <text class="review-title">保留真实经历，优化表达和岗位关键词</text>
        <text class="review-hint">粘贴简历或上传 PDF 后，生成问题标注、替换范文、完整草稿、面试介绍与人岗匹配报告。</text>
        <textarea
          v-model="resumeText"
          class="resume-textarea"
          placeholder="直接粘贴简历文本。未知信息会标为 [待确认]，不会凭空编造经历。"
          auto-height
        />
        <view class="button-row">
          <button class="secondary" :loading="pdfLoading" :disabled="pdfLoading || reviewLoading" @click="chooseResumePdf">上传 PDF 提取文字</button>
          <button class="primary inline-primary" :loading="reviewLoading" :disabled="reviewLoading || pdfLoading" @click="reviewResume">开始批改</button>
        </view>
      <text v-if="reviewError" class="ui-error-tip">{{ reviewError }}</text>
      </view>

      <view v-if="resumeReview" class="result review-result">
        <text class="result-title">简历问题逐条标注</text>
        <text v-for="item in resumeReview.issues" :key="item" class="list-item">- {{ item }}</text>
        <text class="result-title">逐段优化范文</text>
        <text v-for="item in resumeReview.rewriteExamples" :key="item" class="list-item">- {{ item }}</text>
        <text class="result-title">加分关键词</text>
        <text class="keywords">{{ resumeReview.keywords.join(" / ") }}</text>
        <text class="result-title">可复制完整简历文本</text>
        <text class="copy-text">{{ resumeReview.optimizedResumeText }}</text>
        <text class="result-title">1 分钟面试自我介绍</text>
        <text class="copy-text">{{ resumeReview.interviewIntro }}</text>
        <view v-if="resumeReview.customRequirementNotes.length" class="custom-note">
          <text class="block-title">已纳入你的补充需求</text>
          <text v-for="item in resumeReview.customRequirementNotes" :key="item" class="list-item">- {{ item }}</text>
        </view>
        <text class="result-title">人岗匹配分析报告</text>
        <view class="match-score-card">
          <text class="match-score">{{ resumeReview.jobMatchReport.score }}%</text>
          <text class="match-score-label">目标岗位匹配度</text>
        </view>
        <text class="block-title">评分口径</text>
        <text v-for="item in resumeReview.jobMatchReport.scoreBasis" :key="item" class="list-item">- {{ item }}</text>
        <text class="block-title">现有匹配优势</text>
        <text v-for="item in resumeReview.jobMatchReport.matchingAdvantages" :key="item" class="list-item">- {{ item }}</text>
        <text class="block-title">缺失技能清单</text>
        <text v-for="item in resumeReview.jobMatchReport.missingSkills" :key="item" class="list-item">- {{ item }}</text>
        <view v-for="gap in resumeReview.jobMatchReport.priorityGaps" :key="gap.skillName" class="priority-gap ui-long-list-item">
          <text class="priority-gap-title">【需要提升】{{ gap.skillName }}</text>
          <text class="list-item">- 学习方向：{{ gap.learningDirection }}</text>
          <text class="list-item">- 项目练习：{{ gap.projectPractice }}</text>
          <text class="list-item">- 练习任务：{{ gap.practiceTask }}</text>
        </view>
      </view>

      <view v-if="canReviewResume" class="toolkit-card">
        <text class="card-eyebrow">求职工具箱</text>
        <text class="review-title">针对当前身份的专项准备</text>
        <picker :range="adviceTopics" range-key="label" @change="selectAdviceTopic">
          <view class="picker-value">{{ selectedAdviceTopic.label }} <text class="picker-arrow">›</text></view>
        </picker>
        <textarea
          v-model="adviceQuestion"
          class="question-textarea"
          placeholder="可补充具体问题，例如：如何确认公积金基数？"
          auto-height
        />
        <button class="primary primary-action" :loading="adviceLoading" :disabled="adviceLoading" @click="requestCareerAdvice">获取针对性建议</button>
      <text v-if="adviceError" class="ui-error-tip">{{ adviceError }}</text>
      </view>

      <view v-if="careerAdvice" class="result">
        <text class="result-title">{{ careerAdvice.title }}</text>
        <view v-for="section in careerAdvice.sections" :key="section.order" class="plan-block ui-long-list-item">
          <text class="block-title">{{ section.title }}</text>
          <text v-for="item in section.items" :key="item" class="list-item">- {{ item }}</text>
        </view>
      </view>
    </view>
  </scroll-view>
  <OnboardingTour
    :visible="showOnboarding"
    @complete="finishOnboarding"
    @navigate="navigateFromOnboarding"
  />
</template>

<style scoped>
.page { height: 100vh; background: #f4f7fb; }
.page-content { padding: 28rpx 28rpx 72rpx; box-sizing: border-box; }
.hero { padding: 16rpx 4rpx 32rpx; }
.hero-kicker,.card-eyebrow { display: block; color: #5d89c7; font-size: 20rpx; font-weight: 700; letter-spacing: 1.5rpx; }
.title { display: block; margin-top: 8rpx; color: #1d2a3a; font-size: 48rpx; font-weight: 700; line-height: 1.2; }
.subtitle { display: block; margin-top: 12rpx; color: #718096; font-size: 26rpx; line-height: 1.65; }

.search-card,.result,.identity-card,.review-card,.toolkit-card {
  margin-top: 22rpx; padding: 26rpx; background: #ffffff; border: 1rpx solid #e4eaf2;
  border-radius: 22rpx; box-shadow: 0 12rpx 32rpx rgba(38, 65, 102, .08);
}
.search-header,.result-header,.market-card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 18rpx; }
.card-title,.review-title { display: block; margin-top: 8rpx; color: #1d2a3a; font-size: 30rpx; font-weight: 700; line-height: 1.35; }
.search-count { flex-shrink: 0; padding: 6rpx 12rpx; color: #5d89c7; background: #eef5ff; border-radius: 999rpx; font-size: 21rpx; }

.search-shell { position: relative; margin-top: 22rpx; z-index: 3; }
.role-input,.resume-textarea,.question-textarea,.custom-requirement-input,.picker-value {
  width: 100%; box-sizing: border-box; color: #31445a; background: #f7f9fc; border: 1rpx solid #e0e7f0;
  border-radius: 14rpx; font-size: 26rpx;
}
.role-input { height: 88rpx; padding: 0 74rpx 0 22rpx; }
.search-icon { position: absolute; top: 22rpx; right: 24rpx; color: #6c94ca; font-size: 40rpx; line-height: 1; }
.suggestion-popover {
  position: absolute; top: 98rpx; right: 0; left: 0; overflow: hidden; padding: 14rpx;
  background: #fff; border: 1rpx solid #dbe7f5; border-radius: 16rpx; box-shadow: 0 16rpx 38rpx rgba(35, 73, 118, .16);
}
.popover-title { display: block; padding: 6rpx 8rpx 12rpx; color: #7d8da1; font-size: 22rpx; }
.suggestion-button {
  display: flex; align-items: center; justify-content: space-between; width: 100%; margin: 0 0 8rpx;
  padding: 18rpx; color: #1d2a3a; background: #f7faff; border: 1rpx solid transparent; border-radius: 12rpx; text-align: left;
}
.suggestion-button:last-child { margin-bottom: 0; }
.suggestion-name,.suggestion-category,.suggestion-add { display: block; }
.suggestion-name { font-size: 27rpx; font-weight: 600; }.suggestion-category { margin-top: 5rpx; color: #8292a6; font-size: 21rpx; }
.suggestion-add { color: #2d77d1; font-size: 22rpx; }
.suggestion-list-enter-active,.suggestion-list-leave-active { transition: opacity var(--ui-motion-fast) var(--ui-motion-ease), transform var(--ui-motion-fast) var(--ui-motion-ease); }.suggestion-list-enter-from,.suggestion-list-leave-to { opacity: 0; transform: translateY(-6rpx); }

.selected-role-area { margin-top: 20rpx; }
.selected-role-title { display: block; color: #718096; font-size: 23rpx; }
.role-chip-list,.role-tab-list { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 12rpx; }
.role-chip,.role-tab {
  margin: 0; padding: 8rpx 16rpx; color: #2d77d1; background: #edf5ff; border: 1rpx solid #cde0f7;
  border-radius: 999rpx; font-size: 23rpx; line-height: 1.45;
}
.role-tab { max-width: 320rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.custom-requirement-input { min-height: 96rpx; margin-top: 20rpx; padding: 18rpx 20rpx; line-height: 1.6; }
.primary,.secondary { border-radius: 12rpx; font-size: 25rpx; }
.primary { color: #fff; background: #2d77d1; }.secondary { color: #53667b; background: #edf2f7; }
.primary-action { margin-top: 18rpx; }.error { display: block; margin-top: 12rpx; color: #cf4b5d; font-size: 23rpx; line-height: 1.5; }

.identity-prompt { display: block; margin-top: 12rpx; color: #34465b; font-size: 25rpx; font-weight: 600; line-height: 1.55; }
.identity-options { display: flex; flex-direction: column; gap: 12rpx; margin-top: 22rpx; }
.identity-button { display: flex; align-items: center; gap: 14rpx; margin: 0; padding: 18rpx; color: #2e4965; background: #f7faff; border: 1rpx solid #e2ebf5; border-radius: 14rpx; text-align: left; }
.identity-code { display: inline-flex; align-items: center; justify-content: center; width: 38rpx; height: 38rpx; color: #fff; background: #6094d5; border-radius: 50%; font-size: 22rpx; }
.identity-arrow { margin-left: auto; color: #8ca5c2; font-size: 38rpx; line-height: .7; }

.role-tab-list { margin: 0 0 22rpx; padding-bottom: 18rpx; border-bottom: 1rpx solid #e7edf4; }
.role-tab-active { color: #fff; background: #2d77d1; border-color: #2d77d1; }
.role { display: block; margin-top: 8rpx; color: #1d2a3a; font-size: 40rpx; font-weight: 700; line-height: 1.25; }
.identity-name { display: block; margin-top: 8rpx; color: #5d89c7; font-size: 24rpx; font-weight: 600; }
.compact { flex-shrink: 0; min-width: 136rpx; margin: 0; padding: 12rpx 14rpx; font-size: 22rpx; }

.summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12rpx; margin-top: 22rpx; }
.summary-item { min-width: 0; padding: 18rpx; background: #f6f9fd; border: 1rpx solid #e8eef5; border-radius: 14rpx; }
.summary-label { display: block; color: #8393a5; font-size: 21rpx; }.summary-value { display: block; margin-top: 8rpx; color: #2766af; font-size: 25rpx; font-weight: 700; line-height: 1.45; word-break: break-word; }
.summary-skills { color: #3c536c; font-size: 23rpx; font-weight: 600; }
.notice-bar { display: flex; align-items: flex-start; gap: 10rpx; margin-top: 16rpx; padding: 14rpx 16rpx; background: #fff9ee; border-radius: 12rpx; }
.notice-dot { flex-shrink: 0; width: 12rpx; height: 12rpx; margin-top: 9rpx; background: #e8aa50; border-radius: 50%; }
.notice { color: #7c633c; font-size: 23rpx; line-height: 1.6; }

.custom-note,.market-card,.growth-stage,.priority-gap,.target-picker,.resume-callout {
  margin-top: 20rpx; padding: 20rpx; background: #f8fbff; border: 1rpx solid #e1ebf7; border-radius: 16rpx;
}
.block-title { color: #26394d; font-size: 26rpx; font-weight: 700; line-height: 1.45; }
.list-item { display: block; color: #52677d; font-size: 25rpx; line-height: 1.72; word-break: break-word; }
.market-caption { display: block; margin-top: 6rpx; color: #8292a6; font-size: 21rpx; line-height: 1.45; }
.market-notice { display: block; margin-top: 16rpx; color: #55708d; font-size: 23rpx; line-height: 1.55; }
.market-disabled { color: #9b7a45; }
.market-source { display: flex; align-items: flex-start; justify-content: space-between; gap: 14rpx; margin-top: 14rpx; padding-top: 14rpx; border-top: 1rpx solid #e3ebf4; }
.market-source-title,.market-source-text,.market-source-date { display: block; }.market-source-title { color: #2f5e93; font-size: 24rpx; font-weight: 700; }.market-source-text { margin-top: 5rpx; color: #65798d; font-size: 22rpx; line-height: 1.55; }.market-source-date { margin-top: 5rpx; color: #93a1b2; font-size: 20rpx; }
.source-copy { flex-shrink: 0; color: #2d77d1; font-size: 20rpx; }

.result-title { display: block; margin-top: 34rpx; color: #1d2a3a; font-size: 31rpx; font-weight: 700; }
.analysis-section { margin-top: 14rpx; overflow: hidden; border: 1rpx solid #e6edf5; border-radius: 14rpx; }
.analysis-section-header { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; padding: 18rpx; background: #fbfcfe; }
.analysis-section-header > view { display: flex; align-items: center; gap: 12rpx; min-width: 0; }
.analysis-index { display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; width: 40rpx; height: 40rpx; color: #3d79bf; background: #eaf3ff; border-radius: 10rpx; font-size: 20rpx; font-weight: 700; }
.section-toggle { flex-shrink: 0; color: #6e91b8; font-size: 21rpx; }.analysis-section-body { padding: 0 18rpx 18rpx; }
.risk-item { margin-top: 8rpx; padding: 12rpx; color: #a36022; background: #fff8ec; border-radius: 10rpx; }

.growth-stage { border-left: 6rpx solid #76a9e7; }.growth-stage-title { display: block; color: #2b5f9b; font-size: 27rpx; font-weight: 700; }.growth-meta { display: block; margin: 8rpx 0; color: #6e91b8; font-size: 22rpx; }
.identity-plan-title,.follow-up,.keywords { display: block; margin-top: 14rpx; color: #4f6680; font-size: 25rpx; line-height: 1.6; }.plan-block { margin-top: 14rpx; padding: 18rpx; background: #f8fbff; border-radius: 14rpx; }
.resume-callout { background: #f0f7ff; border-color: #cfe4fb; }.resume-callout-title { display: block; color: #245b99; font-size: 28rpx; font-weight: 700; }.resume-callout-text,.target-picker-hint { display: block; margin-top: 10rpx; color: #59728d; font-size: 23rpx; line-height: 1.6; }
.target-picker { background: #fff; }.target-picker-title { display: block; color: #26394d; font-size: 27rpx; font-weight: 700; }.target-role-button { margin-top: 14rpx; color: #286fbf; background: #eff7ff; border: 1rpx solid #d3e7fb; border-radius: 12rpx; text-align: left; font-size: 24rpx; }

.review-hint { display: block; margin-top: 12rpx; color: #718096; font-size: 24rpx; line-height: 1.6; }.resume-textarea { min-height: 190rpx; margin-top: 20rpx; padding: 18rpx; line-height: 1.65; }.question-textarea { min-height: 120rpx; margin-top: 18rpx; padding: 18rpx; line-height: 1.6; }
.button-row { display: flex; gap: 14rpx; margin-top: 16rpx; }.button-row button { flex: 1; padding-right: 8rpx; padding-left: 8rpx; font-size: 22rpx; }.inline-primary { margin-top: 0; }
.copy-text { display: block; margin-top: 14rpx; padding: 18rpx; color: #51677d; background: #f7f9fc; border-radius: 14rpx; font-size: 24rpx; line-height: 1.7; white-space: pre-line; word-break: break-word; }
.match-score-card { display: flex; align-items: baseline; gap: 16rpx; margin-top: 16rpx; padding: 22rpx; background: #eaf4ff; border-radius: 16rpx; }.match-score { color: #2465ad; font-size: 54rpx; font-weight: 700; }.match-score-label { color: #55708d; font-size: 24rpx; }
.priority-gap { background: #fffaf1; border-color: #f5dfb8; }.priority-gap-title { display: block; margin-bottom: 8rpx; color: #a56727; font-size: 26rpx; font-weight: 700; }
.picker-value { display: flex; align-items: center; justify-content: space-between; margin-top: 20rpx; padding: 20rpx; color: #4b6279; }.picker-arrow { color: #7090ad; font-size: 32rpx; line-height: .7; }

@media (max-width: 360px) {
  .page-content { padding-right: 20rpx; padding-left: 20rpx; }
  .summary-grid { grid-template-columns: 1fr; }
  .button-row { flex-direction: column; }
  .market-card-header .compact,.result-header .compact { min-width: 116rpx; font-size: 20rpx; }
}
.hero-actions { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 18rpx; }
.planner-entry { margin-top: 0; padding: 0 24rpx; line-height: 62rpx; border: 1rpx solid #9bc8ff; border-radius: 999rpx; background: rgba(255,255,255,.76); color: #1677ff; font-size: 24rpx; }
.loading-skeleton { min-height: 250rpx; }.skeleton-title,.skeleton-line { height: 24rpx; margin-top: 20rpx; border-radius: 8rpx; background: linear-gradient(90deg, #edf2f7 25%, #f8fafc 40%, #edf2f7 65%); background-size: 400% 100%; animation: shimmer 1.2s ease-in-out infinite; }.skeleton-title { width: 52%; height: 36rpx; margin-top: 0; }.skeleton-line.short { width: 48%; }@keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: 0 0; } }
.account-entry { display: flex; justify-content: flex-end; margin-top: -8rpx; }
@media (prefers-reduced-motion: reduce) { .suggestion-list-enter-active,.suggestion-list-leave-active { transition: none; }.suggestion-list-enter-from,.suggestion-list-leave-to { transform: none; } }
</style>
