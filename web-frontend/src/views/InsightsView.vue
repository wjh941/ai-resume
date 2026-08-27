<script setup lang="ts">
import { BookOpenCheck, Search } from "lucide-vue-next"
import { computed, inject, ref } from "vue"

import { requestApi } from "../lib/api"
import AsyncButton from "../components/AsyncButton.vue"
import type { WorkspaceView } from "../components/WebSidebar.vue"
import { CAPABILITIES_KEY, defaultCapabilities, getCapabilities, isCapabilityEnabled, type Capabilities } from "../lib/capabilities"

type Report = {
  mode: "simplified" | "professional"
  summary: string
  actions: string[]
  source_notice: string
  evidence: Array<{ title: string; detail: string; date: string; scope: string }>
  upgrade_notice?: string
}

const roleName = ref("")
const year = ref(String(new Date().getFullYear() - 1))
const reportMode = ref<"simplified" | "professional">("simplified")
const capabilities = inject(CAPABILITIES_KEY, ref<Capabilities>(defaultCapabilities()))
const capabilityOverride = ref<Capabilities | null>(null)
const effectiveCapabilities = computed(() => capabilityOverride.value ?? capabilities.value)
const jobMatchingEnabled = computed(() => isCapabilityEnabled(effectiveCapabilities.value, "jobMatching"))
const capabilityHint = computed(() => effectiveCapabilities.value.jobMatching.notice)
const capabilityNotice = ref("")
const capabilityRefreshing = ref(false)
const report = ref<Report | null>(null)
const loading = ref(false)
const error = ref("")
const emit = defineEmits<{ navigate: [view: WorkspaceView] }>()

async function retryCapabilities() {
  if (capabilityRefreshing.value) return
  capabilityRefreshing.value = true
  try {
    capabilityOverride.value = await getCapabilities()
    capabilityNotice.value = jobMatchingEnabled.value ? "" : capabilityHint.value
  } catch {
    capabilityNotice.value = capabilityHint.value
  } finally {
    capabilityRefreshing.value = false
  }
}

async function queryInsights() {
  if (loading.value) return
  if (!roleName.value.trim()) {
    error.value = "请输入要查询的岗位名称"
    return
  }
  if (reportMode.value === "professional" && !jobMatchingEnabled.value) {
    capabilityNotice.value = capabilityHint.value
    return
  }
  loading.value = true
  error.value = ""
  capabilityNotice.value = ""
  try {
    const response = await requestApi<{ report: Report }>("/api/career/annual-insights/query", {
      method: "POST",
      body: JSON.stringify({ role_name: roleName.value.trim(), year: Number(year.value), report_mode: reportMode.value }),
    })
    report.value = response.report
  } catch {
    error.value = "年度洞察暂时无法查询。请检查权限或稍后重试。"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="view-layout">
    <div class="view-heading"><div><h1 id="insights-title">年度就业洞察</h1><p>按目标岗位和资料年份阅读已归档的公开资料，用于组织准备，而不是替代正式招聘信息。</p></div></div>
    <form class="insight-query decision-surface" :aria-describedby="error ? 'insights-error' : undefined" @submit.prevent="queryInsights">
      <label><span>岗位</span><input v-model.trim="roleName" maxlength="120" placeholder="例如：数据分析师" :aria-invalid="Boolean(error && !roleName.trim())" /></label>
      <label><span>资料年份</span><input v-model="year" type="number" min="2000" max="2100" /></label>
      <div class="mode-switch" role="group" aria-label="洞察表达方式"><button type="button" :disabled="loading" :class="{ 'is-selected': reportMode === 'simplified' }" @click="reportMode = 'simplified'">精简版</button><button type="button" :disabled="loading" :aria-disabled="!jobMatchingEnabled" :class="{ 'is-selected': reportMode === 'professional', 'is-unavailable': !jobMatchingEnabled }" :title="!jobMatchingEnabled ? capabilityHint : undefined" @click="reportMode = 'professional'">专业版</button></div>
      <small v-if="!jobMatchingEnabled" class="mode-notice">{{ capabilityHint }}</small>
      <AsyncButton class="primary-button compact" type="submit" :loading="loading"><Search :size="17" aria-hidden="true" />{{ loading ? "查询中" : "查询洞察" }}</AsyncButton>
    </form>
    <ErrorNotice v-if="error" id="insights-error" :message="error" />
    <ErrorNotice v-if="capabilityNotice" id="insights-capability-error" :message="capabilityNotice">
      <AsyncButton class="notice-action" type="button" :loading="capabilityRefreshing" @click="retryCapabilities">重试能力状态</AsyncButton>
      <AsyncButton class="notice-action" type="button" @click="emit('navigate', 'membership')">查看会员权益</AsyncButton>
    </ErrorNotice>
    <article v-if="report" class="insight-result decision-surface decision-emphasis"><div><span class="report-mode-label">{{ report.mode === 'professional' ? '专业版' : '精简版' }}</span><h2>{{ report.summary }}</h2></div><section><h3>建议行动</h3><ol><li v-for="action in report.actions" :key="action">{{ action }}</li></ol></section><section v-if="report.evidence.length"><h3>资料依据</h3><div class="evidence-list"><article v-for="item in report.evidence" :key="`${item.title}-${item.date}`"><strong>{{ item.title }}</strong><p>{{ item.detail }}</p><small>{{ item.date }} · {{ item.scope }}</small></article></div></section><p class="source-notice">{{ report.source_notice }}</p><p v-if="report.upgrade_notice" class="upgrade-notice">{{ report.upgrade_notice }}</p></article>
    <div v-else-if="!loading" class="empty-board"><BookOpenCheck :size="30" aria-hidden="true" /><div><h2>输入岗位和资料年份</h2><p>精简版提供通俗易懂的行动提示；专业版在拥有权限时会显示资料依据和更完整的行动计划。</p></div></div>
  </section>
</template>
