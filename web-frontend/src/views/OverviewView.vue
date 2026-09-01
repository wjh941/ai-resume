<script setup lang="ts">
import { Activity, ArrowUpRight, CircleCheck, CircleDot, FilePenLine, KanbanSquare, ListChecks } from "lucide-vue-next"
import { computed, nextTick, onMounted, ref } from "vue"
import { ApiRequestError } from "../lib/api"
import { loadOverview, type ContinuationItem, type OverviewState } from "../lib/dashboard"
import AnimatedNumber from "../components/AnimatedNumber.vue"
import AsyncButton from "../components/AsyncButton.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"

const emit = defineEmits<{ navigate: [view: "resume" | "career" | "applications"]; "open-draft": [draftId: string] }>()
const overview = ref<OverviewState | null>(null)
const loading = ref(true)
const error = ref("")
const focusIndex = ref(0)
const focusStatus = ref("")
const activeFocus = computed(() => overview.value?.focusOptions[focusIndex.value] ?? overview.value?.focus)

async function refresh() {
  loading.value = true
  error.value = ""
  try { overview.value = await loadOverview(); focusIndex.value = 0 }
  catch (reason) { error.value = reason instanceof ApiRequestError && reason.status === 401 ? "登录已过期，请退出后重新登录" : "暂时无法读取工作概览，请稍后重试" }
  finally { loading.value = false }
}
function rotateFocus() {
  if (loading.value || !overview.value?.focusOptions.length) return
  focusIndex.value = (focusIndex.value + 1) % overview.value.focusOptions.length
}
function runFocus() {
  if (loading.value || !activeFocus.value) return
  focusStatus.value = `已选择：${activeFocus.value.title}`
  void nextTick(() => emit("navigate", activeFocus.value!.target))
}
function openContinuation(item: ContinuationItem): void {
  focusStatus.value = "宸查€夋嫨锛?" + item.title
  if (item.kind === "resume" && item.id) {
    emit("open-draft", item.id)
    return
  }
  emit("navigate", item.target)
}
onMounted(refresh)
</script>

<template>
  <section class="view-layout">
    <div class="view-heading overview-hero growth-stage">
      <div><div class="section-kicker"><Activity :size="15" aria-hidden="true" />今日工作台</div><h1 id="overview-title">今天先完成一件重要的事</h1><p>把求职资料、目标岗位和投递节奏放在同一处推进。</p></div>
      <div class="heading-actions"><span v-if="!loading && !error" class="sync-status"><CircleCheck :size="15" aria-hidden="true" />数据已同步</span><AsyncButton class="text-action" type="button" :loading="loading" @click="refresh">刷新概览</AsyncButton></div>
    </div>
    <div v-if="loading" class="overview-loading" aria-busy="true" aria-label="正在读取工作概览"><LoadingSpinner class="overview-loading-spinner" label="正在读取工作概览" /><span v-for="index in 3" :key="index" class="overview-skeleton" /></div>
    <ErrorNotice v-else-if="error" :message="error"><AsyncButton class="notice-action" type="button" :loading="loading" @click="refresh">重新读取</AsyncButton></ErrorNotice>
    <div v-else-if="overview" class="overview-workspace">
      <section class="overview-focus" aria-labelledby="focus-title">
        <article class="focus-panel"><p v-if="activeFocus?.dueLabel" class="focus-due">{{ activeFocus.dueLabel }}</p><div class="section-kicker">今日重点</div><!-- 鎹竴浠? --><h2 id="focus-title">今天先完成这一件事</h2><p v-if="activeFocus" class="focus-title">{{ activeFocus.title }}</p><p v-if="activeFocus?.description" class="focus-detail">{{ activeFocus.description }}</p><p v-if="focusStatus" class="focus-status" aria-live="polite">{{ focusStatus }}</p><div class="focus-controls"><button class="focus-action" type="button" :disabled="loading || !activeFocus" @click="runFocus">开始这项行动 <ArrowUpRight :size="17" aria-hidden="true" /></button><button v-if="overview.focusOptions.length > 1" class="text-action" type="button" :disabled="loading" @click="rotateFocus">换一件</button></div></article>
        <div class="progress-list" aria-label="求职进度"><div v-for="item in overview.progress" :key="item.kind" class="progress-row" :data-state="item.state"><CircleCheck v-if="item.state === 'completed'" :size="18" aria-hidden="true" /><CircleDot v-else :size="18" aria-hidden="true" /><span>{{ item.label }}</span><strong>{{ item.state === 'completed' ? '已完成' : item.state === 'in-progress' ? '进行中' : '未开始' }}</strong><button type="button" :disabled="loading" @click="emit('navigate', item.kind)">进入 <ArrowUpRight :size="15" aria-hidden="true" /></button></div></div>
      </section>
      <section class="overview-strip" aria-label="工作概览快照"><article class="metric-block"><span class="metric-icon"><FilePenLine :size="21" aria-hidden="true" /></span><span>简历草稿</span><strong><AnimatedNumber :value="overview.draftCount" /></strong><small>已有内容可继续完善</small></article><article class="metric-block metric-mint"><span class="metric-icon"><ListChecks :size="21" aria-hidden="true" /></span><span>待完成行动</span><strong><AnimatedNumber :value="overview.openTaskCount" /></strong><small>把计划变成下一步动作</small></article><article class="metric-block metric-sky"><span class="metric-icon"><KanbanSquare :size="21" aria-hidden="true" /></span><span>投递记录</span><strong><AnimatedNumber :value="overview.applicationCount" /></strong><small>持续记录每次进展</small></article></section>
      <section class="continue-list" aria-label="继续推进"><div class="section-heading"><div><h2>继续推进</h2><p>从上次停下的地方接着做。</p></div></div><div v-if="overview.hasWorkspaceData && overview.continuations.length" class="continue-items"><div v-for="item in overview.continuations.slice(0, 3)" :key="`${item.kind}-${item.id ?? item.title}`" class="continue-item"><span>{{ item.title }}</span><button type="button" :disabled="loading" :aria-label="`${item.kind === 'resume' ? '缁х画缂栬緫' : '缁х画'} ${item.title}`" @click="openContinuation(item)">{{ item.kind === "resume" ? "缁х画缂栬緫" : "缁х画" }} <ArrowUpRight :size="15" aria-hidden="true" /></button></div></div><p v-else-if="overview.hasWorkspaceData" class="continue-empty">当前没有需要继续的事项。</p><ol v-else class="starter-list"><li v-for="item in [{ label: '完善简历基础信息', target: 'resume' }, { label: '制定下一步行动', target: 'career' }, { label: '记录第一条投递', target: 'applications' }]" :key="item.target"><span>{{ item.label }}</span><button type="button" :disabled="loading" @click="emit('navigate', item.target)">开始 <ArrowUpRight :size="15" aria-hidden="true" /></button></li></ol></section>
    </div>
  </section>
</template>

<style scoped>
.overview-hero .text-action {
  min-height: 44px;
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
}

@media (prefers-reduced-motion: reduce) {
  .overview-hero .text-action {
    transition: none !important;
    transform: none !important;
  }
}
</style>
