<script setup lang="ts">
import { BookmarkPlus, BriefcaseBusiness, Search } from "lucide-vue-next"
import { computed, ref } from "vue"

import { requestApi } from "../lib/api"
import AsyncButton from "../components/AsyncButton.vue"
import type { WorkspaceView } from "../components/WebSidebar.vue"

type JobResult = {
  role_name: string
  salary_by_experience?: Record<string, string>
  responsibilities?: string[]
  hard_requirements?: string[]
  required_skills?: string[]
  report?: { summary?: string; actions?: string[]; source_notice?: string }
}

const roleName = ref("")
const reportMode = ref<"simplified" | "professional">("simplified")
const result = ref<JobResult | null>(null)
const loading = ref(false)
const saving = ref(false)
const error = ref("")
const skills = computed(() => [...(result.value?.required_skills || []), ...(result.value?.hard_requirements || [])].slice(0, 8))
const emit = defineEmits<{ navigate: [view: WorkspaceView] }>()

async function queryRole() {
  if (!roleName.value.trim()) {
    error.value = "请输入要查询的目标岗位"
    return
  }

  loading.value = true
  error.value = ""
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
  if (!result.value) return
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
    <form class="role-query" @submit.prevent="queryRole">
      <label><span>目标岗位</span><input v-model.trim="roleName" maxlength="200" placeholder="例如：数据分析师" /></label>
      <div class="mode-switch" role="group" aria-label="报告表达方式">
        <button type="button" :class="{ 'is-selected': reportMode === 'simplified' }" @click="reportMode = 'simplified'">精简版</button>
        <button type="button" :class="{ 'is-selected': reportMode === 'professional' }" @click="reportMode = 'professional'">专业版</button>
      </div>
      <AsyncButton class="primary-button compact" type="submit" :loading="loading"><Search :size="17" aria-hidden="true" />{{ loading ? "分析中" : "查询岗位" }}</AsyncButton>
    </form>
    <p v-if="error" class="notice-error" role="alert">{{ error }}</p>

    <article v-if="result" class="job-result">
      <div class="result-heading"><div><h2>{{ result.role_name }}</h2><p>{{ result.report?.summary || "根据当前资料整理岗位准备方向。" }}</p></div><div class="heading-actions"><AsyncButton class="text-action" type="button" @click="emit('navigate', 'comparison')">加入岗位对比</AsyncButton><AsyncButton class="text-action" type="button" :loading="saving" @click="favorite"><BookmarkPlus :size="16" aria-hidden="true" />收藏岗位</AsyncButton></div></div>
      <div class="job-columns">
        <section><h3>优先能力</h3><ul class="tag-list"><li v-for="skill in skills" :key="skill">{{ skill }}</li></ul></section>
        <section><h3>核心职责</h3><ul class="plain-list"><li v-for="item in result.responsibilities?.slice(0, 4)" :key="item">{{ item }}</li></ul></section>
        <section><h3>经验参考</h3><dl class="salary-list"><template v-for="(salary, experience) in result.salary_by_experience" :key="experience"><dt>{{ experience }}</dt><dd>{{ salary }}</dd></template></dl></section>
      </div>
      <section class="report-actions"><h3>下一步建议</h3><ol><li v-for="action in result.report?.actions" :key="action">{{ action }}</li></ol><p>{{ result.report?.source_notice }}</p></section>
    </article>
    <div v-else-if="!loading" class="empty-board"><BriefcaseBusiness :size="30" aria-hidden="true" /><div><h2>从一个目标岗位开始</h2><p>查询结果用于组织准备和核验方向，不代表实时岗位数量、薪资区间或录用概率。</p></div></div>
  </section>
</template>
