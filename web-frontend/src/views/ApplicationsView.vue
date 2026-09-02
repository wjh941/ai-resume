<script setup lang="ts">
import { Building2, CalendarClock, ChevronDown, ChevronUp, Clock3, Pencil, Plus, RefreshCw, Save, Trash2, X } from "lucide-vue-next"
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"

import AsyncButton from "../components/AsyncButton.vue"
import ExpandableText from "../components/ExpandableText.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
import ProgressiveListSentinel from "../components/ProgressiveListSentinel.vue"
import { useIncrementalList } from "../composables/useIncrementalList"
import { addTimelineEvent, deleteApplication, listApplications, listTimeline, saveApplication, saveReminder, type ApplicationInput, type ApplicationRecord, type ApplicationStatus } from "../lib/applications"
import { createApplicationFormSnapshot, isApplicationFormDirty, type ApplicationFormValues, type ApplicationTimelineValues } from "../lib/application-form-state"
import { appendTimelineEvent, removeApplication, replaceApplication } from "../lib/application-workflow"
import { runPendingGuardedAction, resolveApplicationsCloseAction, resolveWorkspaceShortcut } from "../lib/keyboard-shortcuts"

const statusLabels: Record<ApplicationStatus, string> = { saved: "待投递", applied: "已投递", screening: "筛选中", interview: "面试中", offer: "已获录用", rejected: "未通过", closed: "已结束" }
const items = ref<ApplicationRecord[]>([])
const loading = ref(true)
const error = ref("")
const editingId = ref<string | null>(null)
const expandedId = ref<string | null>(null)
const pendingKey = ref("")
const filterStatus = ref<"" | ApplicationStatus>("")
const emptyForm: ApplicationFormValues = { company: "", roleName: "", city: "", status: "saved", source: "", appliedAt: "", nextActionAt: "", nextInterviewAt: "", interviewNotes: "", notes: "", contactInfo: "", attachmentRef: "", draftId: "" }
const emptyTimeline: ApplicationTimelineValues = { title: "", description: "", occurredAt: "" }
const form = ref<ApplicationFormValues>({ ...emptyForm })
const timelineForm = ref<ApplicationTimelineValues>({ ...emptyTimeline })
const reminderAt = ref("")
const formBaseline = ref(createApplicationFormSnapshot(form.value, emptyTimeline, ""))
const followupBaseline = ref(createApplicationFormSnapshot(emptyForm, timelineForm.value, reminderAt.value))
const showLeaveConfirmation = ref(false)
const editing = computed(() => editingId.value !== null)
const isFollowupDirty = computed(() => {
  const followupSnapshot = createApplicationFormSnapshot(emptyForm, timelineForm.value, reminderAt.value)
  return isApplicationFormDirty(followupSnapshot, followupBaseline.value)
})
const isDirty = computed(() => {
  const formSnapshot = createApplicationFormSnapshot(form.value, emptyTimeline, "")
  return isApplicationFormDirty(formSnapshot, formBaseline.value) || isFollowupDirty.value
})
const {
  visibleItems: renderedApplications,
  hasMore: hasMoreApplications,
  showMore: showMoreApplications,
  reset: resetVisibleApplications,
} = useIncrementalList(items)

function resetForm(): void {
  editingId.value = null
  form.value = { ...emptyForm }
  formBaseline.value = createApplicationFormSnapshot(form.value, emptyTimeline, "")
  showLeaveConfirmation.value = false
}
function resetFollowup(): void {
  timelineForm.value = { ...emptyTimeline }
  reminderAt.value = ""
  followupBaseline.value = createApplicationFormSnapshot(emptyForm, timelineForm.value, reminderAt.value)
}
function continueEditing(): void { showLeaveConfirmation.value = false }
function discardChanges(): void {
  resetForm()
  resetFollowup()
  expandedId.value = null
  showLeaveConfirmation.value = false
}
function cancelEditing(): void {
  runPendingGuardedAction(loading.value || Boolean(pendingKey.value), () => {
    if (isDirty.value) { showLeaveConfirmation.value = true; return }
    resetForm()
  })
}
function toIso(value: string): string | null { return value ? new Date(value).toISOString() : null }
function toDate(value: string | null): string { return value ? value.slice(0, 10) : "" }
function toDateTime(value: string | null): string { return value ? value.slice(0, 16) : "" }
function collapseTimeline(): void {
  if (isDirty.value) { showLeaveConfirmation.value = true; return }
  expandedId.value = null
  resetFollowup()
  showLeaveConfirmation.value = false
}
function startEdit(item: ApplicationRecord): void {
  if (isDirty.value) { showLeaveConfirmation.value = true; return }
  editingId.value = item.id
  form.value = { company: item.company, roleName: item.roleName, city: item.city, status: item.status, source: item.source, appliedAt: toDate(item.appliedAt), nextActionAt: toDate(item.nextActionAt), nextInterviewAt: toDateTime(item.nextInterviewAt), interviewNotes: item.interviewNotes, notes: item.notes, contactInfo: item.contactInfo, attachmentRef: item.attachmentRef, draftId: item.draftId || "" }
  formBaseline.value = createApplicationFormSnapshot(form.value, emptyTimeline, "")
  resetFollowup()
  showLeaveConfirmation.value = false
  window.scrollTo({ top: 0, behavior: "smooth" })
}
async function refresh(): Promise<void> { loading.value = true; error.value = ""; try { items.value = await listApplications(filterStatus.value ? { status: filterStatus.value } : {}); resetVisibleApplications() } catch { error.value = "暂时无法读取投递记录，请稍后重试" } finally { loading.value = false } }
async function submit(): Promise<void> {
  if (!form.value.roleName.trim() || pendingKey.value) return
  pendingKey.value = editingId.value ? `save:${editingId.value}` : "create"; error.value = ""
  const input: ApplicationInput = { id: editingId.value || "", company: form.value.company.trim() || "[待确认]", roleName: form.value.roleName.trim(), city: form.value.city.trim(), source: form.value.source.trim(), status: form.value.status, appliedAt: form.value.appliedAt || null, nextActionAt: form.value.nextActionAt || null, interviewNotes: form.value.interviewNotes.trim(), draftId: form.value.draftId.trim() || null, notes: form.value.notes.trim(), contactInfo: form.value.contactInfo.trim(), attachmentRef: form.value.attachmentRef.trim(), nextInterviewAt: toIso(form.value.nextInterviewAt) }
  try { const saved = await saveApplication(input); items.value = editingId.value ? replaceApplication(items.value, saved) : [saved, ...items.value]; resetForm(); if (!isFollowupDirty.value) resetFollowup() } catch { error.value = "投递记录暂未保存，请检查填写内容后重试" } finally { pendingKey.value = "" }
}
async function changeStatus(item: ApplicationRecord, status: ApplicationStatus): Promise<void> {
  if (status === item.status || pendingKey.value) return
  pendingKey.value = `status:${item.id}`; error.value = ""
  try { const saved = await saveApplication({ ...item, status }); items.value = replaceApplication(items.value, saved) } catch { error.value = "状态暂未更新，请稍后重试" } finally { pendingKey.value = "" }
}

function handleStatusChange(item: ApplicationRecord, event: Event): void {
  const value = (event.target as HTMLSelectElement).value as ApplicationStatus
  void changeStatus(item, value)
}
async function toggleTimeline(item: ApplicationRecord): Promise<void> {
  if (isDirty.value) { showLeaveConfirmation.value = true; return }
  if (expandedId.value === item.id) { collapseTimeline(); return }
  expandedId.value = item.id
  resetFollowup()
  followupBaseline.value = createApplicationFormSnapshot(emptyForm, timelineForm.value, reminderAt.value)
  if (item.timeline.length || pendingKey.value) return
  pendingKey.value = `timeline-load:${item.id}`
  try { item.timeline = await listTimeline(item.id) } catch { error.value = "暂时无法读取跟进时间线" } finally { pendingKey.value = "" }
}
async function addEvent(item: ApplicationRecord): Promise<void> {
  if (!timelineForm.value.title.trim() || pendingKey.value) return
  pendingKey.value = `timeline-add:${item.id}`
  try { const event = await addTimelineEvent(item.id, { title: timelineForm.value.title.trim(), description: timelineForm.value.description.trim(), occurredAt: toIso(timelineForm.value.occurredAt) || new Date().toISOString() }); Object.assign(item, appendTimelineEvent(item, event)); timelineForm.value = { ...emptyTimeline }; followupBaseline.value = createApplicationFormSnapshot(emptyForm, timelineForm.value, reminderAt.value); showLeaveConfirmation.value = false } catch { error.value = "跟进事件暂未保存，请稍后重试" } finally { pendingKey.value = "" }
}
async function setReminder(item: ApplicationRecord): Promise<void> {
  if (!reminderAt.value || pendingKey.value) return
  pendingKey.value = `reminder:${item.id}`
  try { await saveReminder(item.id, toIso(reminderAt.value) || reminderAt.value); item.nextActionAt = reminderAt.value.slice(0, 10); reminderAt.value = ""; followupBaseline.value = createApplicationFormSnapshot(emptyForm, timelineForm.value, reminderAt.value); showLeaveConfirmation.value = false } catch { error.value = "提醒暂未保存，请稍后重试" } finally { pendingKey.value = "" }
}
async function remove(item: ApplicationRecord): Promise<void> {
  if (pendingKey.value) return
  if (isDirty.value) { showLeaveConfirmation.value = true; return }
  if (!window.confirm("确认删除这条投递记录吗？")) return
  pendingKey.value = `delete:${item.id}`
  try { await deleteApplication(item.id); items.value = removeApplication(items.value, item.id); expandedId.value = null; resetFollowup() } catch { error.value = "投递记录暂未删除，请稍后重试" } finally { pendingKey.value = "" }
}
function handleShortcut(event: KeyboardEvent): void {
  const action = resolveApplicationsCloseAction(
    resolveWorkspaceShortcut(event),
    loading.value || Boolean(pendingKey.value),
    editing.value,
    expandedId.value !== null,
  )
  if (!action) return
  event.preventDefault()
  if (action === "reset") cancelEditing()
  else collapseTimeline()
}

function handleBeforeUnload(event: BeforeUnloadEvent): void {
  event.preventDefault()
  event.returnValue = ""
}

onMounted(() => {
  window.addEventListener("keydown", handleShortcut)
  void refresh()
})
watch(isDirty, (dirty) => {
  if (dirty) window.addEventListener("beforeunload", handleBeforeUnload)
  else window.removeEventListener("beforeunload", handleBeforeUnload)
})
onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleShortcut)
  window.removeEventListener("beforeunload", handleBeforeUnload)
})
</script>

<template>
  <section class="view-layout">
    <div class="view-heading"><div><h1 id="applications-title">投递管理</h1><p>保存投递意向、跟进状态和面试安排，让每一次行动都可复盘。</p></div><AsyncButton class="text-action" type="button" :loading="loading" @click="refresh"><RefreshCw :size="16" aria-hidden="true" />刷新</AsyncButton></div>
    <form class="application-form workbench-form" :aria-describedby="error ? 'applications-error' : undefined" @submit.prevent="submit">
      <label><span>公司</span><input v-model.trim="form.company" maxlength="200" placeholder="例如：示例科技" /></label>
      <label><span>岗位</span><input v-model.trim="form.roleName" required maxlength="160" placeholder="例如：产品运营" :aria-invalid="Boolean(error && !form.roleName.trim())" /></label>
      <label><span>城市</span><input v-model.trim="form.city" maxlength="120" placeholder="例如：上海" /></label>
      <label><span>状态</span><select v-model="form.status"><option v-for="(label, value) in statusLabels" :key="value" :value="value">{{ label }}</option></select></label>
      <AsyncButton class="primary-button compact" type="submit" :loading="pendingKey === 'create' || pendingKey.startsWith('save:')"><Save v-if="editing" :size="17" aria-hidden="true" /><Plus v-else :size="17" aria-hidden="true" />{{ editing ? "保存修改" : "新增记录" }}</AsyncButton>
      <AsyncButton v-if="editing" class="text-action compact" type="button" :disabled="loading || Boolean(pendingKey)" :aria-disabled="loading || Boolean(pendingKey) || undefined" @click="cancelEditing"><X :size="15" aria-hidden="true" />取消编辑</AsyncButton>
    </form>
    <div v-if="showLeaveConfirmation" class="application-leave-confirmation" role="alert" aria-live="polite">
      <p>当前有未保存的投递信息，确定要离开编辑吗？</p>
      <div class="application-leave-confirmation-actions">
        <AsyncButton class="text-action compact" type="button" @click="continueEditing">继续编辑</AsyncButton>
        <AsyncButton class="danger-action compact" type="button" :disabled="loading || Boolean(pendingKey)" :aria-disabled="loading || Boolean(pendingKey) || undefined" @click="discardChanges">放弃并返回</AsyncButton>
      </div>
    </div>
    <div class="application-toolbar"><label><span>筛选状态</span><select v-model="filterStatus" :disabled="loading" @change="refresh"><option value="">全部状态</option><option v-for="(label, value) in statusLabels" :key="value" :value="value">{{ label }}</option></select></label><span class="toolbar-hint">共 {{ items.length }} 条记录</span></div>
    <ErrorNotice v-if="error" id="applications-error" :message="error"><AsyncButton class="notice-action" type="button" :loading="loading" @click="refresh">重试</AsyncButton></ErrorNotice>
    <div v-else-if="loading" class="content-skeleton application-loading" aria-busy="true"><LoadingSpinner class="content-loading-spinner" label="正在读取投递记录" /><span /><span /></div>
    <div v-else-if="items.length" class="application-table record-surface">
      <article v-for="item in renderedApplications" :key="item.id" class="application-record">
        <div class="application-row"><span class="record-symbol record-sky"><Building2 :size="20" aria-hidden="true" /></span><div><h2><ExpandableText :text="item.roleName" :lines="1" :expand-at="36" label="岗位名称" /></h2><p><ExpandableText :text="[item.company, item.city].filter(Boolean).join(' · ')" :lines="1" :expand-at="44" label="公司与城市" /></p></div><select class="status-select" :value="item.status" :disabled="Boolean(pendingKey)" @change="handleStatusChange(item, $event)"><option v-for="(label, value) in statusLabels" :key="value" :value="value">{{ label }}</option></select><small>{{ item.nextInterviewAt || item.nextActionAt || "尚未设置下一步" }}</small><div class="record-actions"><AsyncButton class="text-action compact" type="button" :disabled="Boolean(pendingKey)" :title="`编辑 ${item.company} 的 ${item.roleName}`" :aria-label="`编辑 ${item.company} 的 ${item.roleName}`" @click="startEdit(item)"><Pencil :size="15" aria-hidden="true" />编辑</AsyncButton><AsyncButton class="text-action compact" type="button" :loading="pendingKey === `timeline-load:${item.id}`" :disabled="Boolean(pendingKey)" :title="`查看 ${item.company} 的 ${item.roleName} 时间线`" :aria-label="`查看 ${item.company} 的 ${item.roleName} 时间线`" @click="toggleTimeline(item)"><ChevronUp v-if="expandedId === item.id" :size="15" aria-hidden="true" /><ChevronDown v-else :size="15" aria-hidden="true" />时间线</AsyncButton><AsyncButton class="danger-action compact" type="button" :loading="pendingKey === `delete:${item.id}`" :disabled="Boolean(pendingKey)" :title="`删除 ${item.company} 的 ${item.roleName}`" :aria-label="`删除 ${item.company} 的 ${item.roleName}`" @click="remove(item)"><Trash2 :size="15" aria-hidden="true" />删除</AsyncButton></div></div>
        <div v-if="expandedId === item.id" class="application-followup"><div class="followup-grid"><div><h3>跟进记录</h3><ol v-if="item.timeline.length" class="timeline-list"><li v-for="event in item.timeline" :key="event.id"><strong>{{ event.title }}</strong><small>{{ event.occurredAt }}</small><p v-if="event.description">{{ event.description }}</p></li></ol><p v-else class="source-notice">暂时没有时间线记录。</p></div><div class="followup-actions"><h3>添加跟进</h3><label><span>标题</span><input v-model.trim="timelineForm.title" maxlength="240" placeholder="例如：完成一面" /></label><label><span>时间</span><input v-model="timelineForm.occurredAt" type="datetime-local" /></label><label><span>说明</span><textarea v-model.trim="timelineForm.description" rows="2" maxlength="4000" /></label><AsyncButton class="primary-button compact" type="button" :loading="pendingKey === `timeline-add:${item.id}`" :disabled="Boolean(pendingKey)" @click="addEvent(item)"><Clock3 :size="15" aria-hidden="true" />添加事件</AsyncButton><h3>设置提醒</h3><label><span>提醒时间</span><input v-model="reminderAt" type="datetime-local" /></label><AsyncButton class="text-action compact" type="button" :loading="pendingKey === `reminder:${item.id}`" :disabled="Boolean(pendingKey)" @click="setReminder(item)"><CalendarClock :size="15" aria-hidden="true" />保存提醒</AsyncButton></div></div></div>
      </article>
      <ProgressiveListSentinel :has-more="hasMoreApplications" @more="showMoreApplications" />
    </div>
    <div v-else class="empty-board"><span class="empty-board-icon" aria-hidden="true"><Building2 :size="24" aria-hidden="true" /></span><div><h2>还没有投递记录</h2><p>在确认岗位与公司信息后，先保存一条待投递记录，再持续补充状态和复盘信息。</p><p>可直接使用上方表单新增第一条记录。</p></div></div>
  </section>
</template>
