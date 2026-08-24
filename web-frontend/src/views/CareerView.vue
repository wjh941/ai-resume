<script setup lang="ts">
import { CalendarDays, Check, Plus, RefreshCw } from "lucide-vue-next"
import { onMounted, ref } from "vue"

import { requestApi } from "../lib/api"
import AsyncButton from "../components/AsyncButton.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import type { WorkspaceView } from "../components/WebSidebar.vue"

type CareerTask = {
  id: string
  title: string
  description?: string
  due_date?: string | null
  status: string
}

const planId = "web-workspace"
const tasks = ref<CareerTask[]>([])
const title = ref("")
const dueDate = ref("")
const loading = ref(true)
const saving = ref(false)
const pendingTaskId = ref<string | null>(null)
const error = ref("")
const emit = defineEmits<{ navigate: [view: WorkspaceView] }>()

async function refresh() {
  loading.value = true
  error.value = ""
  try {
    tasks.value = (await requestApi<{ items: CareerTask[] }>(`/api/career/tasks?plan_id=${planId}`)).items
  } catch {
    error.value = "暂时无法读取行动清单，请稍后重试"
  } finally {
    loading.value = false
  }
}

async function addTask() {
  if (!title.value.trim()) {
    error.value = "请先填写一项可执行的行动"
    return
  }

  saving.value = true
  error.value = ""
  try {
    const task = await requestApi<CareerTask>("/api/career/tasks", {
      method: "POST",
      body: JSON.stringify({ plan_id: planId, title: title.value.trim(), due_date: dueDate.value || null, status: "pending" }),
    })
    tasks.value = [task, ...tasks.value]
    title.value = ""
    dueDate.value = ""
  } catch {
    error.value = "行动暂未保存，请检查登录状态后重试"
  } finally {
    saving.value = false
  }
}

async function toggleTask(task: CareerTask) {
  const status = task.status === "completed" ? "pending" : "completed"
  pendingTaskId.value = task.id
  try {
    const updated = await requestApi<CareerTask>(`/api/career/tasks/${task.id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    })
    tasks.value = tasks.value.map((item) => item.id === task.id ? updated : item)
  } catch {
    error.value = "状态未更新，请稍后重试"
  } finally {
    pendingTaskId.value = null
  }
}

onMounted(refresh)
</script>

<template>
  <section class="view-layout">
    <div class="view-heading">
      <div><h1 id="career-title">职业规划</h1><p>把职业建议拆解为能在本周完成的小行动，并保留完成记录。</p></div>
      <div class="heading-actions"><AsyncButton class="text-action" type="button" :loading="loading" @click="refresh"><RefreshCw :size="16" aria-hidden="true" />刷新</AsyncButton><AsyncButton class="text-action" type="button" @click="emit('navigate', 'comparison')">比较岗位</AsyncButton></div>
    </div>

    <form class="inline-form" @submit.prevent="addTask">
      <label><span>新增行动</span><input v-model.trim="title" required maxlength="240" placeholder="例如：整理一个可展示的项目成果" /></label>
      <label><span>计划完成日</span><input v-model="dueDate" type="date" /></label>
      <AsyncButton class="primary-button compact" type="submit" :loading="saving"><Plus :size="17" aria-hidden="true" />{{ saving ? "保存中" : "加入清单" }}</AsyncButton>
    </form>

    <p v-if="error" class="notice-error" role="alert">{{ error }}</p>
    <div v-else-if="loading" class="content-skeleton" aria-busy="true"><LoadingSpinner class="content-loading-spinner" label="正在读取行动清单" /><span /><span /></div>
    <div v-else-if="tasks.length" class="task-list">
      <article v-for="task in tasks" :key="task.id" class="task-row" :class="{ 'is-complete': task.status === 'completed' }">
        <AsyncButton class="task-check" type="button" :loading="pendingTaskId === task.id" :title="task.status === 'completed' ? '标记为未完成' : '标记为已完成'" :aria-label="task.status === 'completed' ? '标记为未完成' : '标记为已完成'" @click="toggleTask(task)"><Check :size="16" aria-hidden="true" /></AsyncButton>
        <div><h2>{{ task.title }}</h2><p v-if="task.description">{{ task.description }}</p></div>
        <span v-if="task.due_date" class="due-date"><CalendarDays :size="15" aria-hidden="true" />{{ task.due_date }}</span>
      </article>
    </div>
    <div v-else class="empty-board"><CalendarDays :size="30" aria-hidden="true" /><div><h2>还没有行动项</h2><p>从一件能在本周完成的事开始，例如补充一个项目成果或梳理目标岗位要求。</p></div></div>
  </section>
</template>
