<script setup lang="ts">
import { FilePenLine, RefreshCw } from "lucide-vue-next"
import { onMounted, ref } from "vue"

import { requestApi } from "../lib/api"
import AsyncButton from "../components/AsyncButton.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"

type Draft = {
  id: string
  job_title?: string
  template_id?: string
  updated_at?: string
}

const drafts = ref<Draft[]>([])
const loading = ref(true)
const error = ref("")

async function refresh() {
  loading.value = true
  error.value = ""
  try {
    drafts.value = (await requestApi<{ items: Draft[] }>("/api/draft/list")).items
  } catch {
    error.value = "暂时无法读取简历草稿，请稍后重试"
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
</script>

<template>
  <section class="view-layout">
    <div class="view-heading">
      <div><h1 id="resume-title">简历中心</h1><p>集中查看已保存的简历草稿，确保每段经历都能说明你的真实贡献。</p></div>
      <AsyncButton class="text-action" type="button" :loading="loading" @click="refresh"><RefreshCw :size="16" aria-hidden="true" />刷新</AsyncButton>
    </div>

    <p v-if="error" class="notice-error" role="alert">{{ error }}</p>
    <div v-else-if="loading" class="content-skeleton" aria-busy="true"><LoadingSpinner class="content-loading-spinner" label="正在读取简历草稿" /><span /><span /><span /></div>
    <div v-else-if="drafts.length" class="record-list">
      <article v-for="draft in drafts" :key="draft.id" class="record-row">
        <span class="record-symbol record-coral"><FilePenLine :size="21" aria-hidden="true" /></span>
        <div><h2>{{ draft.job_title || "未命名简历" }}</h2><p>模板：{{ draft.template_id || "默认模板" }} · 最近保存：{{ draft.updated_at || "时间待同步" }}</p></div>
        <span class="record-tag">草稿</span>
      </article>
    </div>
    <div v-else class="empty-board">
      <FilePenLine :size="30" aria-hidden="true" />
      <div><h2>还没有简历草稿</h2><p>请先在小程序的“简历中心”创建第一份草稿。独立 Web 工作台会在这里同步展示和管理它。</p></div>
    </div>
  </section>
</template>
