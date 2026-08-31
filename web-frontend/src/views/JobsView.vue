<script setup lang="ts">
import { BookmarkPlus, BriefcaseBusiness, Search } from "lucide-vue-next"
import { computed, inject, ref, watch } from "vue"

import { requestApi } from "../lib/api"
import AsyncButton from "../components/AsyncButton.vue"
import ExpandableText from "../components/ExpandableText.vue"
import type { WorkspaceView } from "../components/WebSidebar.vue"
import { CAPABILITIES_KEY, createCapabilityContext, isCapabilityEnabled } from "../lib/capabilities"

type JobResult = {
  role_name: string
  salary_by_experience?: Record<string, string>
  responsibilities?: string[]
  hard_requirements?: string[]
  required_skills?: string[]
  bonus_skills?: string[]
  career_route?: string[]
  version?: number
  report?: {
    mode?: "simplified" | "professional"
    summary?: string
    actions?: string[]
    source_notice?: string
    upgrade_notice?: string
    evidence?: Array<{ type?: string; title?: string; detail?: string; date?: string; scope?: string }>
  }
}

const roleName = ref("")
const reportMode = ref<"simplified" | "professional">("simplified")
const context = inject(CAPABILITIES_KEY) ?? createCapabilityContext()
const jobMatchingEnabled = computed(() => isCapabilityEnabled(context.capabilities.value, "jobMatching"))
const jobMatchingState = computed<"loading" | "real" | "demo" | "disabled">(() => {
  if (context.refreshing.value) return "loading"
  const capability = context.capabilities.value.jobMatching
  if (!capability.enabled || capability.mode === "disabled") return "disabled"
  return capability.mode
})
const professionalModeLabel = computed(() => jobMatchingState.value === "demo" ? "专业版（演示）" : "专业版")
const capabilityHint = computed(() => context.capabilities.value.jobMatching.notice)
const professionalModeReason = computed(() => jobMatchingState.value === "loading" ? "检查中，请稍候。" : capabilityHint.value)
const showProfessionalReason = computed(() => jobMatchingState.value === "loading" || jobMatchingState.value === "disabled")
const demoSourceNotice = "本地/演示数据不代表实时职位或真实市场洞察。"
const capabilityNotice = ref("")
const capabilityRefreshing = computed(() => context.refreshing.value)
const result = ref<JobResult | null>(null)
const loading = ref(false)
const saving = ref(false)
const error = ref("")
const roleFieldError = ref("")
const unique = (items: Array<string | undefined>): string[] => [...new Set(items.filter((item): item is string => Boolean(item?.trim())).map((item) => item.trim()))]
const requiredSkills = computed(() => unique(result.value?.required_skills || []))
const bonusSkills = computed(() => unique(result.value?.bonus_skills || []))
const hardRequirements = computed(() => unique(result.value?.hard_requirements || []))
const responsibilities = computed(() => unique(result.value?.responsibilities || []))
const careerRoute = computed(() => unique(result.value?.career_route || []))
const interviewChecks = computed(() => {
  const requirements = hardRequirements.value.map((item) => ({
    label: "门槛核验",
    prompt: `请用一个真实案例证明你具备“${item}”，说明场景、你的具体动作、结果和可核验材料。`,
  }))
  const roleWork = responsibilities.value.map((item) => ({
    label: "职责追问",
    prompt: `如果负责“${item}”，你会如何拆解目标、定义交付标准，并用什么指标复盘？`,
  }))
  return [...requirements, ...roleWork]
})
const reportEvidence = computed(() => result.value?.report?.evidence || [])
const reportActions = computed(() => result.value?.report?.actions || [])
const hasProfessionalReport = computed(() => result.value?.report?.mode === "professional")
const emit = defineEmits<{ navigate: [view: WorkspaceView] }>()

async function retryCapabilities() {
  if (context.refreshing.value) return
  try {
    await context.refresh()
    capabilityNotice.value = jobMatchingEnabled.value ? "" : capabilityHint.value
  } catch {
    // Keep the current notice and state when refresh fails.
  }
}

watch(jobMatchingEnabled, (enabled, wasEnabled) => {
  if (wasEnabled && !enabled && reportMode.value === "professional") reportMode.value = "simplified"
  if (!wasEnabled && enabled) capabilityNotice.value = ""
})

watch(roleName, (value) => {
  if (value.trim()) roleFieldError.value = ""
})

async function queryRole() {
  if (loading.value) return
  if (!roleName.value.trim()) {
    roleFieldError.value = "请输入要查询的目标岗位"
    error.value = ""
    return
  }
  if (reportMode.value === "professional" && !jobMatchingEnabled.value) {
    capabilityNotice.value = capabilityHint.value
    return
  }

  loading.value = true
  roleFieldError.value = ""
  error.value = ""
  capabilityNotice.value = ""
  try {
    result.value = await requestApi<JobResult>("/api/job/query", {
      method: "POST",
      body: JSON.stringify({ role_name: roleName.value.trim(), report_mode: reportMode.value }),
    })
  } catch {
    error.value = "岗位分析暂时不可用。请确认 AI 服务已配置，或稍后重试。"
  } finally {
    loading.value = false
  }
}

async function favorite() {
  if (!result.value || saving.value) return
  saving.value = true
  try {
    await requestApi("/api/job-collection/favorites", {
      method: "POST",
      body: JSON.stringify({ role_name: result.value.role_name }),
    })
  } catch {
    error.value = "岗位收藏未保存，请稍后重试"
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="view-layout">
    <div class="view-heading"><div><h1 id="jobs-title">岗位机会</h1><p>围绕一个明确的岗位梳理能力要求，再回到真实经历补齐准备。</p></div></div>
    <form class="role-query workbench-form" :aria-describedby="error ? 'jobs-error' : undefined" @submit.prevent="queryRole">
      <label><span>目标岗位</span><input v-model.trim="roleName" maxlength="200" placeholder="例如：数据分析师" :aria-invalid="Boolean(roleFieldError)" :aria-describedby="roleFieldError ? 'jobs-role-error' : undefined" /><small v-if="roleFieldError" id="jobs-role-error" class="form-error">{{ roleFieldError }}</small></label>
      <div class="mode-switch" role="group" aria-label="报告表达方式">
        <button type="button" :disabled="loading" :class="{ 'is-selected': reportMode === 'simplified' }" @click="reportMode = 'simplified'">精简版</button>
        <button type="button" :disabled="loading || !jobMatchingEnabled || capabilityRefreshing" :aria-disabled="!jobMatchingEnabled || capabilityRefreshing" :aria-describedby="showProfessionalReason ? 'jobs-professional-mode-reason' : undefined" :class="{ 'is-selected': reportMode === 'professional', 'is-unavailable': !jobMatchingEnabled }" :title="!jobMatchingEnabled ? capabilityHint : undefined" @click="reportMode = 'professional'">{{ professionalModeLabel }}</button>
        <small v-if="showProfessionalReason" id="jobs-professional-mode-reason" class="mode-notice">{{ professionalModeReason }}</small>
        <div v-if="!jobMatchingEnabled" class="mode-recovery-actions">
          <AsyncButton class="notice-action" type="button" :loading="capabilityRefreshing" @click="retryCapabilities">重试服务状态</AsyncButton>
          <AsyncButton class="notice-action" type="button" @click="emit('navigate', 'membership')">查看会员权益</AsyncButton>
        </div>
      </div>
      <AsyncButton class="primary-button compact" type="submit" :loading="loading"><Search :size="17" aria-hidden="true" />{{ loading ? "分析中" : "查询岗位" }}</AsyncButton>
    </form>
    <ErrorNotice v-if="error" id="jobs-error" :message="error" />
    <ErrorNotice v-if="capabilityNotice" id="jobs-capability-error" :message="capabilityNotice">
      <AsyncButton class="notice-action" type="button" :loading="capabilityRefreshing" @click="retryCapabilities">重试能力状态</AsyncButton>
      <AsyncButton class="notice-action" type="button" @click="emit('navigate', 'membership')">查看会员权益</AsyncButton>
    </ErrorNotice>

    <article v-if="result" class="job-result">
      <div class="result-heading">
        <div>
          <h2><ExpandableText :text="result.role_name" :lines="1" :expand-at="36" label="岗位名称" /></h2>
          <p><ExpandableText :text="result.report?.summary || '根据当前资料整理岗位准备方向。'" :lines="4" :expand-at="96" label="岗位分析摘要" /></p>
        </div>
        <div class="heading-actions"><AsyncButton class="text-action" type="button" @click="emit('navigate', 'comparison')">加入岗位对比</AsyncButton><AsyncButton class="text-action" type="button" :loading="saving" @click="favorite"><BookmarkPlus :size="16" aria-hidden="true" />收藏岗位</AsyncButton></div>
      </div>

      <div class="job-reference-notice" role="note"><strong>先看结论</strong><span>{{ result.report?.source_notice || "以下内容来自结构化岗位知识，用于准备和复核正式 JD。" }}</span><span v-if="hasProfessionalReport && jobMatchingState === 'demo'" class="source-notice demo-source-notice">{{ demoSourceNotice }}</span></div>

      <div class="job-intelligence-grid">
        <section class="job-intelligence-card job-intelligence-card-primary"><div class="job-card-heading"><h3>硬性门槛</h3><span>筛选优先级高</span></div><ul v-if="hardRequirements.length" class="plain-list"><li v-for="item in hardRequirements" :key="item">{{ item }}</li></ul><p v-else class="job-muted">暂未提供硬性门槛，请以正式 JD 为准。</p></section>
        <section class="job-intelligence-card"><div class="job-card-heading"><h3>优先能力</h3><span>建议先补齐</span></div><ul v-if="requiredSkills.length" class="tag-list"><li v-for="skill in requiredSkills" :key="skill">{{ skill }}</li></ul><p v-else class="job-muted">暂未提供必备技能。</p></section>
        <section class="job-intelligence-card"><div class="job-card-heading"><h3>加分技能</h3><span>面试差异化</span></div><ul v-if="bonusSkills.length" class="tag-list job-bonus-list"><li v-for="skill in bonusSkills" :key="skill">{{ skill }}</li></ul><p v-else class="job-muted">暂无额外加分技能，先把优先能力做成证据。</p></section>
      </div>

      <section class="job-detail-section"><div class="job-section-heading"><div><h3>核心职责</h3><p>每项职责都应对应一段真实经历、交付物和结果数据。</p></div><strong>{{ responsibilities.length }} 项</strong></div><div v-if="responsibilities.length" class="responsibility-list"><article v-for="(item, index) in responsibilities" :key="item"><span>{{ String(index + 1).padStart(2, '0') }}</span><div><strong>{{ item }}</strong><p>准备一条证据：说明你在什么场景完成了这项工作、采用什么方法、交付了什么结果。</p></div></article></div><p v-else class="job-muted">暂未提供职责描述，请补充正式 JD 后再做匹配。</p></section>

      <div class="job-columns job-columns-refined">
        <section><div class="job-section-heading"><h3>经验参考</h3><span>非实时薪资承诺</span></div><dl v-if="result.salary_by_experience && Object.keys(result.salary_by_experience).length" class="salary-list"><template v-for="(salary, experience) in result.salary_by_experience" :key="experience"><dt>{{ experience }}</dt><dd>{{ salary }}</dd></template></dl><p v-else class="job-muted">暂无薪酬参考，请以目标城市和企业 offer 核验。</p><p class="job-footnote">核验时逐项确认固定薪资、绩效规则、试用期折扣、社保公积金基数和发薪日。</p></section>
        <section><div class="job-section-heading"><h3>职业路径</h3><span>{{ careerRoute.length }} 个阶段</span></div><ol v-if="careerRoute.length" class="career-route-list"><li v-for="(stage, index) in careerRoute" :key="stage"><span>{{ index + 1 }}</span>{{ stage }}</li></ol><p v-else class="job-muted">暂未提供职业路径。</p></section>
      </div>

      <section class="job-interview-panel"><div class="job-section-heading"><div><h3>面试核验清单</h3><p>不要只背技能名，按“场景—动作—结果—证据”准备回答。</p></div><strong>{{ interviewChecks.length }} 题</strong></div><div v-if="interviewChecks.length" class="interview-check-list"><details v-for="(check, index) in interviewChecks" :key="check.prompt" :open="index === 0"><summary><span>{{ String(index + 1).padStart(2, '0') }}</span><b>{{ check.label }}</b></summary><p>{{ check.prompt }}</p></details></div><p v-else class="job-muted">暂无可生成的核验问题，请先补充岗位职责或要求。</p></section>

      <section class="report-actions"><div class="job-section-heading"><div><h3>下一步建议</h3><p v-if="hasProfessionalReport">专业版已结合岗位要点整理完整行动路径。</p><p v-else>先完成下面三步，再根据真实 JD 调整优先级。</p></div><span class="report-mode-label">{{ hasProfessionalReport ? professionalModeLabel : '精简版' }}</span></div><ol v-if="reportActions.length"><li v-for="action in reportActions" :key="action">{{ action }}</li></ol><p v-else class="job-muted">暂无行动建议，请先整理一条与目标岗位相关的真实经历。</p><p>{{ result.report?.source_notice }}</p><p v-if="!hasProfessionalReport && result.report?.upgrade_notice" class="upgrade-notice">{{ result.report.upgrade_notice }}</p><details v-if="reportEvidence.length" class="report-evidence"><summary>查看专业证据映射（{{ reportEvidence.length }} 条）</summary><ul class="plain-list"><li v-for="evidence in reportEvidence" :key="`${evidence.title}-${evidence.scope}`"><strong>{{ evidence.title || '岗位要点' }}</strong><span>{{ evidence.detail }}</span></li></ul></details></section>
    </article>
    <div v-else-if="!loading" class="empty-board"><span class="empty-board-icon" aria-hidden="true"><BriefcaseBusiness :size="24" aria-hidden="true" /></span><div><h2>从一个目标岗位开始</h2><p>查询结果用于组织准备和核验方向，不代表实时岗位数量、薪资区间或录用概率。</p><p>输入具体岗位名称后开始整理能力要求。</p></div></div>
  </section>
</template>
