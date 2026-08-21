<script setup lang="ts">
import { ArrowUpRight, FilePenLine, KanbanSquare, ListChecks } from "lucide-vue-next"
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
    <div class="view-heading">
      <div><h1>今天先完成一件重要的事</h1><p>把求职资料、目标岗位和投递节奏放在同一处推进。</p></div>
      <button class="text-action" type="button" :disabled="loading" @click="refresh">刷新概览</button>
    </div>

    <p v-if="error" class="notice-error" role="alert">{{ error }}</p>
    <div v-else class="overview-strip" :aria-busy="loading">
      <article class="metric-block"><FilePenLine :size="23" aria-hidden="true" /><span>简历草稿</span><strong>{{ overview?.draftCount ?? "-" }}</strong></article>
      <article class="metric-block metric-mint"><ListChecks :size="23" aria-hidden="true" /><span>待完成行动</span><strong>{{ overview?.openTaskCount ?? "-" }}</strong></article>
      <article class="metric-block metric-sky"><KanbanSquare :size="23" aria-hidden="true" /><span>投递记录</span><strong>{{ overview?.applicationCount ?? "-" }}</strong></article>
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
