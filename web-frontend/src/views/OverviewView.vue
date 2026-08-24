<script setup lang="ts">
import { Activity, ArrowUpRight, CircleCheck, FilePenLine, KanbanSquare, ListChecks } from "lucide-vue-next"
import { onMounted, ref } from "vue"

import { ApiRequestError } from "../lib/api"
import { loadOverview, type OverviewState } from "../lib/dashboard"

const emit = defineEmits<{
  navigate: [view: "resume" | "career" | "applications"]
}>()

const overview = ref<OverviewState | null>(null)
const loading = ref(true)
const error = ref("")

async function refresh() {
  loading.value = true
  error.value = ""
  try {
    overview.value = await loadOverview()
  } catch (reason) {
    error.value = reason instanceof ApiRequestError && reason.status === 401
      ? "登录已过期，请退出后重新登录"
      : "暂时无法读取工作概览，请稍后重试"
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
</script>

<template>
  <section class="view-layout">
    <div class="view-heading overview-hero">
      <div>
        <div class="section-kicker"><Activity :size="15" aria-hidden="true" />今日工作台</div>
        <h1>今天先完成一件重要的事</h1>
        <p>把求职资料、目标岗位和投递节奏放在同一处推进。</p>
      </div>
      <div class="heading-actions">
        <span v-if="!loading && !error" class="sync-status"><CircleCheck :size="15" aria-hidden="true" />数据已同步</span>
        <button class="text-action" type="button" :disabled="loading" @click="refresh">刷新概览</button>
      </div>
    </div>

    <div v-if="loading" class="overview-loading" aria-busy="true" aria-label="正在读取工作概览">
      <span v-for="index in 3" :key="index" class="overview-skeleton" />
    </div>
    <div v-else-if="error" class="notice-error notice-with-action" role="alert">
      <span>{{ error }}</span><button class="notice-action" type="button" @click="refresh">重新读取</button>
    </div>
    <div v-else class="overview-strip" aria-live="polite">
      <article class="metric-block"><span class="metric-icon"><FilePenLine :size="21" aria-hidden="true" /></span><span>简历草稿</span><strong>{{ overview?.draftCount ?? "-" }}</strong><small>已有内容可继续完善</small></article>
      <article class="metric-block metric-mint"><span class="metric-icon"><ListChecks :size="21" aria-hidden="true" /></span><span>待完成行动</span><strong>{{ overview?.openTaskCount ?? "-" }}</strong><small>把计划变成下一步动作</small></article>
      <article class="metric-block metric-sky"><span class="metric-icon"><KanbanSquare :size="21" aria-hidden="true" /></span><span>投递记录</span><strong>{{ overview?.applicationCount ?? "-" }}</strong><small>持续记录每次进展</small></article>
    </div>

    <section class="action-route" aria-label="求职下一步">
      <div><h2>从准备到投递，按自己的节奏推进</h2><p>先补齐可验证的信息，再确定目标岗位，最后安排投递与复盘。</p></div>
      <div class="route-actions">
        <button type="button" @click="emit('navigate', 'resume')"><span>整理简历</span><ArrowUpRight :size="17" aria-hidden="true" /></button>
        <button type="button" @click="emit('navigate', 'career')"><span>安排行动</span><ArrowUpRight :size="17" aria-hidden="true" /></button>
        <button type="button" @click="emit('navigate', 'applications')"><span>记录投递</span><ArrowUpRight :size="17" aria-hidden="true" /></button>
      </div>
    </section>
  </section>
</template>
