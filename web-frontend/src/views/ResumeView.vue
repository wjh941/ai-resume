<script setup lang="ts">
import { Copy, FilePenLine, Pencil, Plus, RefreshCw, Trash2, X } from "lucide-vue-next"
import { computed, ref } from "vue"

import { ApiRequestError } from "../lib/api"
import { getApiErrorMessage } from "../lib/api-error"
import { copyDraft, deleteDraft, DRAFT_PAGE_SIZE, listDraftsPage, saveDraft, type DraftRecord, type TemplateId } from "../lib/drafts"
import { prependDraft, removeDraftById } from "../lib/draft-workflow"
import { formatDateTime, templateLabel } from "../lib/format"
import { createEmptyDraftInput } from "../lib/resume-draft"
import { useApiResource } from "../composables/useApiResource"
import AsyncButton from "../components/AsyncButton.vue"
import ExpandableText from "../components/ExpandableText.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import type { WorkspaceView } from "../components/WebSidebar.vue"

const emit = defineEmits<{
  "open-draft": [draftId: string]
  navigate: [view: WorkspaceView]
}>()

const drafts = ref<DraftRecord[]>([])
const totalDrafts = ref(0)
const pageIndex = ref(0)
const totalPages = computed(() => Math.max(1, Math.ceil(totalDrafts.value / DRAFT_PAGE_SIZE)))
const pendingAction = ref<"copy" | "delete" | "">("")
const pendingDraftId = ref("")
const createOpen = ref(false)
const creating = ref(false)
const createError = ref("")
const createLimitReached = ref(false)
const newJobTitle = ref("")
const newTemplate = ref<TemplateId>("business")

const {
  loading,
  error,
  run: refresh,
  retry: retryFailedRequest,
  retryable,
  clearRetry,
} = useApiResource(async () => {
  // 列表走服务端分页(每页 20 条,total 驱动页码);编辑/详情仍由编辑视图按需拉取。
  const page = await listDraftsPage(DRAFT_PAGE_SIZE, pageIndex.value * DRAFT_PAGE_SIZE)
  drafts.value = page.items
  totalDrafts.value = page.total
  return true
}, { fallbackMessage: "暂时无法读取简历草稿，请稍后重试", immediate: true })

async function goToPage(index: number): Promise<void> {
  if (loading.value) return
  const target = Math.min(Math.max(index, 0), totalPages.value - 1)
  if (target === pageIndex.value) return
  pageIndex.value = target
  await refresh()
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
  clearRetry()
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
    createError.value = getApiErrorMessage(reason, "简历暂未创建，请稍后重试")
  } finally {
    creating.value = false
  }
}

async function copy(item: DraftRecord): Promise<void> {
  if (pendingAction.value) return
  pendingAction.value = "copy"
  pendingDraftId.value = item.id
  clearRetry()
  error.value = ""
  try {
    const copied = await copyDraft(item.id)
    // 服务端按 updated_at 倒序返回:首页直接本地前插即可与下一页刷新结果一致;
    // 非首页时副本落在更前的页,当前页内容整体后移一位,重新拉取当前页保持正确。
    if (pageIndex.value === 0) {
      drafts.value = prependDraft(drafts.value, copied)
      totalDrafts.value += 1
    } else {
      await refresh()
    }
  } catch (reason) {
    error.value = getApiErrorMessage(reason, "无法复制简历草稿，请稍后重试")
  } finally {
    pendingAction.value = ""
    pendingDraftId.value = ""
  }
}

async function remove(item: DraftRecord): Promise<void> {
  if (pendingAction.value || !window.confirm("确认删除这份简历草稿吗？")) return
  pendingAction.value = "delete"
  pendingDraftId.value = item.id
  clearRetry()
  error.value = ""
  try {
    await deleteDraft(item.id)
    drafts.value = removeDraftById(drafts.value, item.id)
    totalDrafts.value = Math.max(0, totalDrafts.value - 1)
    // 删掉的是当前页最后一条且还有前一页时,回退一页重新拉取。
    if (!drafts.value.length && pageIndex.value > 0) {
      pageIndex.value -= 1
      await refresh()
    }
  } catch (reason) {
    error.value = getApiErrorMessage(reason, "无法删除简历草稿，请稍后重试")
  } finally {
    pendingAction.value = ""
    pendingDraftId.value = ""
  }
}
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

    <ErrorNotice v-if="error" :message="error"><AsyncButton v-if="retryable" class="notice-action" type="button" :loading="loading" @click="retryFailedRequest">重试读取</AsyncButton></ErrorNotice>
    <div v-else-if="loading" class="content-skeleton" aria-busy="true"><LoadingSpinner class="content-loading-spinner" label="正在读取简历草稿" /><span /><span /><span /></div>
    <div v-else-if="drafts.length" class="record-list record-surface">
      <article v-for="draft in drafts" :key="draft.id" class="record-row">
        <span class="record-symbol record-coral"><FilePenLine :size="21" aria-hidden="true" /></span>
        <div><h2><ExpandableText :text="draft.jobTitle || '未命名简历'" :lines="1" :expand-at="36" label="简历名称" /></h2><p>模板：{{ templateLabel(draft.templateId) }} · 最近保存：{{ formatDateTime(draft.updatedAt, "时间待同步") }}</p></div>
        <div class="record-actions">
          <AsyncButton class="text-action compact" type="button" :title="`编辑 ${draft.jobTitle || '未命名简历'}`" :aria-label="`编辑 ${draft.jobTitle || '未命名简历'}`" @click="emit('open-draft', draft.id)"><Pencil :size="15" aria-hidden="true" />编辑</AsyncButton>
          <AsyncButton class="text-action compact" type="button" :loading="pendingAction === 'copy' && pendingDraftId === draft.id" :disabled="Boolean(pendingAction)" :title="`复制 ${draft.jobTitle || '未命名简历'}`" :aria-label="`复制 ${draft.jobTitle || '未命名简历'}`" @click="copy(draft)"><Copy :size="15" aria-hidden="true" />复制</AsyncButton>
          <AsyncButton class="danger-action compact" type="button" :loading="pendingAction === 'delete' && pendingDraftId === draft.id" :disabled="Boolean(pendingAction)" :title="`删除 ${draft.jobTitle || '未命名简历'}`" :aria-label="`删除 ${draft.jobTitle || '未命名简历'}`" @click="remove(draft)"><Trash2 :size="15" aria-hidden="true" />删除</AsyncButton>
        </div>
      </article>
      <nav v-if="totalPages > 1" class="draft-pagination" aria-label="简历草稿分页">
        <AsyncButton class="text-action compact" type="button" :disabled="loading || pageIndex === 0" aria-label="上一页" @click="goToPage(pageIndex - 1)">上一页</AsyncButton>
        <span class="draft-pagination-status">第 {{ pageIndex + 1 }} / {{ totalPages }} 页 · 共 {{ totalDrafts }} 份</span>
        <AsyncButton class="text-action compact" type="button" :disabled="loading || pageIndex >= totalPages - 1" aria-label="下一页" @click="goToPage(pageIndex + 1)">下一页</AsyncButton>
      </nav>
    </div>
    <div v-else class="empty-board">
      <span class="empty-board-icon" aria-hidden="true"><FilePenLine :size="24" aria-hidden="true" /></span>
      <div><h2>还没有简历草稿</h2><p>从一个目标岗位开始，创建第一份简历并逐步补充真实经历。</p><p>本机编辑内容会自动保留，手动保存后同步到服务端。</p><AsyncButton class="primary-button compact" type="button" data-action="new-resume" @click="openCreate"><Plus :size="16" aria-hidden="true" />新建简历</AsyncButton></div>
    </div>
  </section>
</template>
