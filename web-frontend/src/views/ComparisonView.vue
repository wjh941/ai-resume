<script setup lang="ts">
import { ArrowRight, GitCompareArrows, Map, RefreshCw } from "lucide-vue-next"
import { computed, onMounted, ref } from "vue"

import AsyncButton from "../components/AsyncButton.vue"
import CapsuleMultiSelect from "../components/CapsuleMultiSelect.vue"
import ComparisonRolePicker from "../components/ComparisonRolePicker.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import { ApiRequestError } from "../lib/api"
import { compareRoles, isCareerProfileMissingError, loadCareerRecommendations, type CareerComparisonResponse, type CareerRecommendation } from "../lib/career"
import type { WorkspaceView } from "../components/WebSidebar.vue"

const emit = defineEmits<{ navigate: [view: WorkspaceView] }>()
const recommendations = ref<CareerRecommendation[]>([])
const selected = ref<string[]>([])
const result = ref<CareerComparisonResponse | null>(null)
const loading = ref(true)
const comparing = ref(false)
const error = ref("")
const needsMembership = ref(false)
const profileMissing = ref(false)
const comparisonSuccess = ref(false)
const roles = computed(() => recommendations.value.map((item) => item.role.roleName).filter((role, index, all) => Boolean(role) && all.indexOf(role) === index))

async function refresh(): Promise<void> {
  loading.value = true; error.value = ""; needsMembership.value = false; profileMissing.value = false
  try {
    const response = await loadCareerRecommendations()
    recommendations.value = [...response.tiers.stretch, ...response.tiers.stable, ...response.tiers.safe]
  } catch (caught) {
    if (isCareerProfileMissingError(caught)) {
      profileMissing.value = true
      return
    }
    error.value = caught instanceof Error ? caught.message : "暂时无法读取岗位推荐，请稍后重试"
  }
  finally { loading.value = false }
}
async function compare(): Promise<void> {
  if (selected.value.length < 2 || selected.value.length > 4 || comparing.value) return
  comparing.value = true; comparisonSuccess.value = false; error.value = ""; needsMembership.value = false
  try { result.value = await compareRoles(selected.value) } catch (caught) { if (caught instanceof ApiRequestError && caught.status === 403) needsMembership.value = true; error.value = caught instanceof Error ? caught.message : "岗位对比暂未完成，请稍后重试" } finally { comparing.value = false }
  if (result.value) comparisonSuccess.value = true
}
onMounted(refresh)
</script>

<template>
  <section class="view-layout comparison-view">
    <div class="view-heading"><div><h1 id="comparison-title">岗位对比</h1><p>把目标岗位放在同一张表里，比较匹配程度、证据缺口和下一步行动。</p></div><AsyncButton class="text-action" type="button" :loading="loading" @click="refresh"><RefreshCw :size="16" aria-hidden="true" />刷新推荐</AsyncButton></div>
    <ErrorNotice v-if="error && !profileMissing" :message="error" />
    <div v-if="loading" class="content-skeleton comparison-loading" aria-busy="true"><LoadingSpinner class="content-loading-spinner" label="正在读取岗位推荐" /><CapsuleMultiSelect :options="[]" :selected="[]" loading :skeleton-count="6" /><span /></div>
    <div v-else-if="profileMissing" class="empty-board profile-missing" role="status">
      <span class="empty-board-icon" aria-hidden="true"><Map :size="24" /></span>
      <div>
        <span class="section-kicker">先完成资料</span>
        <h2>还没有职业资料</h2>
        <p>岗位推荐需要你的职业资料。请先在小程序的职业规划中保存资料，再回到这里继续比较岗位。</p>
        <AsyncButton class="notice-action" type="button" @click="emit('navigate', 'career')">查看职业规划 <ArrowRight :size="15" aria-hidden="true" /></AsyncButton>
      </div>
    </div>
    <template v-else>
      <ComparisonRolePicker v-model:selected="selected" :roles="roles" :max-selectable="4" :pending="comparing" :success="comparisonSuccess" @submit="compare" />
      <div v-if="needsMembership" class="notice-with-action report-actions"><p>当前岗位对比能力需要会员权益，已保留你选择的岗位。</p><AsyncButton class="notice-action" type="button" @click="emit('navigate', 'membership')">查看会员权益</AsyncButton></div>
      <section v-if="result" class="comparison-result decision-surface decision-emphasis"><div class="result-heading"><div><span class="section-kicker"><GitCompareArrows :size="14" aria-hidden="true" />对比结果</span><h2>{{ result.recommendationNotice }}</h2><p>共同优势：{{ result.commonStrengths.join("、") || "暂无" }}</p></div><AsyncButton class="text-action" type="button" @click="emit('navigate', 'applications')">去投递管理</AsyncButton></div><div class="comparison-grid"><article v-for="item in result.items" :key="item.role.roleName" class="comparison-card"><div class="comparison-card-heading"><div><h3>{{ item.role.roleName }}</h3><small>{{ item.matchingLevel }}</small></div><strong>{{ item.totalScore }}</strong></div><p>{{ item.role.description }}</p><section><h4>匹配优势</h4><ul class="plain-list"><li v-for="advantage in item.matchingAdvantages" :key="advantage">{{ advantage }}</li></ul></section><section><h4>待补证据</h4><ul class="plain-list"><li v-for="skill in item.missingSkills" :key="skill">{{ skill }}</li></ul></section><p v-if="item.riskNotice" class="upgrade-notice">风险：{{ item.riskNotice }}</p><details><summary>行动计划</summary><ol class="plain-list"><li v-for="action in [...item.actionPlan.sevenDay, ...item.actionPlan.thirtyDay, ...item.actionPlan.ninetyDay]" :key="action">{{ action }}</li></ol></details></article></div></section>
      <div v-else class="empty-board"><GitCompareArrows :size="28" aria-hidden="true" /><div><h2>选择岗位后开始对比</h2><p>从推荐岗位中选择至少两个，结果会保留在当前页面。</p></div></div>
    </template>
  </section>
</template>
