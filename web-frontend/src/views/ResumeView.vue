<script setup lang="ts">
import { Copy, FilePenLine, Pencil, RefreshCw, Trash2 } from "lucide-vue-next"
import { onMounted, ref } from "vue"

import { copyDraft, deleteDraft, listDrafts, type DraftRecord } from "../lib/drafts"
import { prependDraft, removeDraftById } from "../lib/draft-workflow"
import AsyncButton from "../components/AsyncButton.vue"
import ExpandableText from "../components/ExpandableText.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import ProgressiveListSentinel from "../components/ProgressiveListSentinel.vue"
import { useIncrementalList } from "../composables/useIncrementalList"

const emit = defineEmits<{
  "open-draft": [draftId: string]
}>()

const drafts = ref<DraftRecord[]>([])
const loading = ref(true)
const error = ref("")
const pendingAction = ref<"copy" | "delete" | "">("")
const pendingDraftId = ref("")
const {
  visibleItems: renderedDrafts,
  hasMore: hasMoreDrafts,
  showMore: showMoreDrafts,
  reset: resetVisibleDrafts,
} = useIncrementalList(drafts)

async function refresh() {
  loading.value = true
  error.value = ""
  try {
    drafts.value = await listDrafts()
    resetVisibleDrafts()
  } catch {
    error.value = "暂时无法读取简历草稿，请稍后重试"
  } finally {
    loading.value = false
  }
}

async function copy(item: DraftRecord): Promise<void> {
  if (pendingAction.value) return
  pendingAction.value = "copy"
  pendingDraftId.value = item.id
  error.value = ""
  try {
    drafts.value = prependDraft(drafts.value, await copyDraft(item.id))
  } catch {
    error.value = "无法复制简历草稿，请稍后重试"
  } finally {
    pendingAction.value = ""
    pendingDraftId.value = ""
  }
}

async function remove(item: DraftRecord): Promise<void> {
  if (pendingAction.value || !window.confirm("确认删除这份简历草稿吗？")) return
  pendingAction.value = "delete"
  pendingDraftId.value = item.id
  error.value = ""
  try {
    await deleteDraft(item.id)
    drafts.value = removeDraftById(drafts.value, item.id)
  } catch {
    error.value = "无法删除简历草稿，请稍后重试"
  } finally {
    pendingAction.value = ""
    pendingDraftId.value = ""
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

    <ErrorNotice v-if="error" :message="error" />
    <div v-else-if="loading" class="content-skeleton" aria-busy="true"><LoadingSpinner class="content-loading-spinner" label="正在读取简历草稿" /><span /><span /><span /></div>
    <div v-else-if="drafts.length" class="record-list">
      <article v-for="draft in renderedDrafts" :key="draft.id" class="record-row">
        <span class="record-symbol record-coral"><FilePenLine :size="21" aria-hidden="true" /></span>
        <div><h2><ExpandableText :text="draft.jobTitle || '未命名简历'" :lines="1" :expand-at="36" label="简历名称" /></h2><p>模板：{{ draft.templateId || "默认模板" }} · 最近保存：{{ draft.updatedAt || "时间待同步" }}</p></div>
        <div class="record-actions">
          <AsyncButton class="text-action compact" type="button" :title="`编辑 ${draft.jobTitle || '未命名简历'}`" :aria-label="`编辑 ${draft.jobTitle || '未命名简历'}`" @click="emit('open-draft', draft.id)"><Pencil :size="15" aria-hidden="true" />编辑</AsyncButton>
          <AsyncButton class="text-action compact" type="button" :loading="pendingAction === 'copy' && pendingDraftId === draft.id" :disabled="Boolean(pendingAction)" :title="`复制 ${draft.jobTitle || '未命名简历'}`" :aria-label="`复制 ${draft.jobTitle || '未命名简历'}`" @click="copy(draft)"><Copy :size="15" aria-hidden="true" />复制</AsyncButton>
          <AsyncButton class="danger-action compact" type="button" :loading="pendingAction === 'delete' && pendingDraftId === draft.id" :disabled="Boolean(pendingAction)" :title="`删除 ${draft.jobTitle || '未命名简历'}`" :aria-label="`删除 ${draft.jobTitle || '未命名简历'}`" @click="remove(draft)"><Trash2 :size="15" aria-hidden="true" />删除</AsyncButton>
        </div>
      </article>
      <ProgressiveListSentinel :has-more="hasMoreDrafts" @more="showMoreDrafts" />
    </div>
    <div v-else class="empty-board">
      <span class="empty-board-icon" aria-hidden="true"><FilePenLine :size="24" aria-hidden="true" /></span>
      <div><h2>还没有简历草稿</h2><p>请先在小程序的“简历中心”创建第一份草稿。独立 Web 工作台会在这里同步展示和管理它。</p><p>本机编辑内容会自动保留，手动保存后同步到服务端。</p></div>
    </div>
  </section>
</template>
