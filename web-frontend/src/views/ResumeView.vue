<script setup lang="ts">
import { Copy, FilePenLine, Pencil, Plus, RefreshCw, Trash2, X } from "lucide-vue-next"
import { onMounted, ref } from "vue"

import { ApiRequestError } from "../lib/api"
import { copyDraft, deleteDraft, listDrafts, saveDraft, type DraftRecord, type TemplateId } from "../lib/drafts"
import { prependDraft, removeDraftById } from "../lib/draft-workflow"
import { createEmptyDraftInput } from "../lib/resume-draft"
import AsyncButton from "../components/AsyncButton.vue"
import ExpandableText from "../components/ExpandableText.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import ProgressiveListSentinel from "../components/ProgressiveListSentinel.vue"
import { useIncrementalList } from "../composables/useIncrementalList"
import type { WorkspaceView } from "../components/WebSidebar.vue"

const emit = defineEmits<{
  "open-draft": [draftId: string]
  navigate: [view: WorkspaceView]
}>()

const drafts = ref<DraftRecord[]>([])
const loading = ref(true)
const error = ref("")
const pendingAction = ref<"copy" | "delete" | "">("")
const pendingDraftId = ref("")
const createOpen = ref(false)
const creating = ref(false)
const createError = ref("")
const createLimitReached = ref(false)
const newJobTitle = ref("")
const newTemplate = ref<TemplateId>("business")
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

function openCreate(): void {
  createOpen.value = true
  createError.value = ""
  createLimitReached.value = false
}

function closeCreate(): void {
  if (creating.value) return
  createOpen.value = false
  createError.value = ""
}

async function create(): Promise<void> {
  if (creating.value) return
  if (!newJobTitle.value.trim()) {
    createError.value = "请填写目标岗位或简历名称"
    createLimitReached.value = false
    return
  }

  creating.value = true
  createError.value = ""
  createLimitReached.value = false
  try {
    const draft = await saveDraft(createEmptyDraftInput(newJobTitle.value, newTemplate.value))
    createOpen.value = false
    emit("open-draft", draft.id)
  } catch (reason) {
    createLimitReached.value = reason instanceof ApiRequestError && reason.status === 403
    createError.value = reason instanceof Error && reason.message
      ? reason.message
      : "简历暂未创建，请稍后重试"
  } finally {
    creating.value = false
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
      <div class="heading-actions">
        <AsyncButton class="text-action" type="button" :loading="loading" @click="refresh"><RefreshCw :size="16" aria-hidden="true" />刷新</AsyncButton>
        <AsyncButton class="primary-button compact" type="button" :disabled="loading || creating" data-action="new-resume" @click="openCreate"><Plus :size="16" aria-hidden="true" />新建简历</AsyncButton>
      </div>
    </div>

    <form v-if="createOpen" class="resume-create-form decision-surface" @submit.prevent="create">
      <div class="panel-heading"><div><span class="section-kicker">开始一份新简历</span><h2>先填写目标岗位</h2></div><AsyncButton class="text-action compact" type="button" :disabled="creating" aria-label="关闭新建简历" @click="closeCreate"><X :size="16" aria-hidden="true" /></AsyncButton></div>
      <div class="resume-create-fields">
        <label><span>目标岗位或简历名称</span><input v-model.trim="newJobTitle" name="new-job-title" required maxlength="160" placeholder="例如：数据分析师" /></label>
        <label><span>简历模板</span><select v-model="newTemplate"><option value="business">商务模板</option><option value="technology">技术模板</option><option value="graduate">毕业生模板</option><option value="analytics">分析模板</option></select></label>
        <AsyncButton class="primary-button compact" type="submit" :loading="creating" data-action="create-resume"><Plus :size="16" aria-hidden="true" />{{ creating ? "创建中" : "创建并编辑" }}</AsyncButton>
      </div>
      <ErrorNotice v-if="createError" :message="createError"><AsyncButton v-if="createLimitReached" class="notice-action" type="button" @click="emit('navigate', 'membership')">查看会员权益</AsyncButton><AsyncButton v-else class="notice-action" type="button" @click="create">重试</AsyncButton></ErrorNotice>
    </form>

    <ErrorNotice v-if="error" :message="error" />
    <div v-else-if="loading" class="content-skeleton" aria-busy="true"><LoadingSpinner class="content-loading-spinner" label="正在读取简历草稿" /><span /><span /><span /></div>
    <div v-else-if="drafts.length" class="record-list record-surface">
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
      <div><h2>还没有简历草稿</h2><p>从一个目标岗位开始，创建第一份简历并逐步补充真实经历。</p><p>本机编辑内容会自动保留，手动保存后同步到服务端。</p><AsyncButton class="primary-button compact" type="button" data-action="new-resume" @click="openCreate"><Plus :size="16" aria-hidden="true" />新建简历</AsyncButton></div>
    </div>
  </section>
</template>
