<script setup lang="ts">
import { computed, onMounted, ref } from "vue"

import {
  createApplicationTimelineEvent,
  deleteApplication,
  listApplicationTimeline,
  listApplications,
  saveInterviewReminder,
} from "../../services/application-api"
import { useApplicationsStore } from "../../stores/applications"
import { getClientId } from "../../stores/session"
import type {
  ApplicationInput,
  ApplicationRecord,
  ApplicationStatus,
} from "../../types/application"
import { filterApplications } from "../../utils/application-filter"

type Query = { roleName?: string; city?: string; draftId?: string }

const statuses: Array<{ value: "all" | ApplicationStatus; label: string }> = [
  { value: "all", label: "全部" },
  { value: "saved", label: "待准备" },
  { value: "applied", label: "已投递" },
  { value: "screening", label: "筛选中" },
  { value: "interview", label: "面试" },
  { value: "offer", label: "录用" },
  { value: "rejected", label: "未通过" },
  { value: "closed", label: "已结束" },
]
const statusOptions = statuses.slice(1)
const applicationsStore = useApplicationsStore()
const applications = ref<ApplicationRecord[]>([])
const selectedStatus = ref<"all" | ApplicationStatus>("all")
const loading = ref(false)
const saving = ref(false)
const error = ref("")
const form = ref<ApplicationInput>(emptyForm())
const interviewDate = ref("")
const timelineDraft = ref({ applicationId: "", title: "", description: "", occurredAt: "" })
const reminderAt = ref("")

const visibleApplications = computed(() => filterApplications(applications.value, selectedStatus.value).filter((item) => (
  !interviewDate.value || item.nextInterviewAt?.startsWith(interviewDate.value)
)))
const dueCount = computed(() => applications.value.filter((item) => (
  Boolean(item.nextActionAt) && !["offer", "rejected", "closed"].includes(item.status)
)).length)
const upcomingInterviews = computed(() => applications.value
  .filter((item) => {
    const interviewAt = Date.parse(item.nextInterviewAt || "")
    return Number.isFinite(interviewAt) && interviewAt >= Date.now()
  })
  .sort((left, right) => Date.parse(left.nextInterviewAt || "") - Date.parse(right.nextInterviewAt || "")))

function emptyForm(query: Query = {}): ApplicationInput {
  return {
    clientId: getClientId(),
    company: "[待确认]",
    roleName: query.roleName || "",
    city: query.city || "",
    source: "官网",
    status: "saved",
    appliedAt: null,
    nextActionAt: null,
    interviewNotes: "",
    draftId: query.draftId || null,
    notes: "",
    contactInfo: "",
    attachmentRef: "",
    nextInterviewAt: null,
  }
}

function queryFromPage(): Query {
  const current = getCurrentPages().at(-1) as { options?: Query } | undefined
  return current?.options ?? {}
}

async function load() {
  loading.value = true
  error.value = ""
  try {
    applications.value = await listApplications(getClientId())
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "投递记录加载失败"
  } finally {
    loading.value = false
  }
}

async function syncPending() {
  const result = await applicationsStore.syncPending()
  if (result.synced) {
    await load()
    uni.showToast({ title: `已同步 ${result.synced} 条记录`, icon: "success" })
  } else if (result.remaining) {
    uni.showToast({ title: "网络仍不可用，待同步记录已保留", icon: "none" })
  }
}

function selectStatus(event: Event) {
  const index = Number((event as unknown as { detail?: { value?: string } }).detail?.value)
  if (statusOptions[index]) form.value.status = statusOptions[index].value as ApplicationStatus
}

function edit(item: ApplicationRecord) {
  form.value = {
    id: item.id,
    clientId: item.clientId,
    company: item.company,
    roleName: item.roleName,
    city: item.city,
    source: item.source,
    status: item.status,
    appliedAt: item.appliedAt,
    nextActionAt: item.nextActionAt,
    interviewNotes: item.interviewNotes,
    draftId: item.draftId,
    notes: item.notes,
    contactInfo: item.contactInfo || "",
    attachmentRef: item.attachmentRef || "",
    nextInterviewAt: item.nextInterviewAt || null,
  }
  uni.pageScrollTo({ scrollTop: 0, duration: 180 })
}

function resetForm() {
  form.value = emptyForm(queryFromPage())
}

async function save() {
  if (!form.value.roleName.trim()) {
    uni.showToast({ title: "请填写目标岗位", icon: "none" })
    return
  }
  saving.value = true
  const result = await applicationsStore.saveOrQueue({ ...form.value, clientId: getClientId() })
  saving.value = false
  if (result.queued) {
    uni.showToast({ title: "网络不可用，已保存到本机待同步", icon: "none" })
    resetForm()
    return
  }
  await load()
  resetForm()
  uni.showToast({ title: "投递计划已保存", icon: "success" })
}

function beginTimeline(item: ApplicationRecord) {
  timelineDraft.value = {
    applicationId: item.id,
    title: "",
    description: "",
    occurredAt: new Date().toISOString(),
  }
}

async function saveTimeline() {
  const draft = timelineDraft.value
  if (!draft.applicationId || !draft.title.trim() || !draft.occurredAt) {
    uni.showToast({ title: "请填写时间线标题和时间", icon: "none" })
    return
  }
  try {
    await createApplicationTimelineEvent(draft.applicationId, {
      title: draft.title,
      description: draft.description,
      occurredAt: draft.occurredAt,
    })
    const item = applications.value.find((current) => current.id === draft.applicationId)
    if (item) item.timeline = await listApplicationTimeline(draft.applicationId)
    timelineDraft.value = { applicationId: "", title: "", description: "", occurredAt: "" }
    uni.showToast({ title: "时间线已添加", icon: "success" })
  } catch (reason) {
    uni.showToast({ title: reason instanceof Error ? reason.message : "时间线保存失败，请稍后重试", icon: "none" })
  }
}

async function saveReminder() {
  if (!form.value.id || !reminderAt.value) {
    uni.showToast({ title: "请先编辑投递记录并填写提醒时间", icon: "none" })
    return
  }
  try {
    await saveInterviewReminder(form.value.id, reminderAt.value)
    reminderAt.value = ""
    uni.showToast({ title: "面试提醒已保存", icon: "success" })
  } catch (reason) {
    uni.showToast({ title: reason instanceof Error ? reason.message : "提醒保存失败，请稍后重试", icon: "none" })
  }
}

function remove(item: ApplicationRecord) {
  uni.showModal({
    title: "删除投递记录",
    content: `确认删除“${item.roleName}”的投递计划吗？`,
    success: async (result) => {
      if (!result.confirm) return
      try {
        await deleteApplication(getClientId(), item.id)
        applications.value = applications.value.filter((current) => current.id !== item.id)
        if (form.value.id === item.id) resetForm()
        uni.showToast({ title: "投递记录已删除", icon: "success" })
      } catch (reason) {
        uni.showToast({
          title: reason instanceof Error ? reason.message : "删除失败，请稍后重试",
          icon: "none",
        })
      }
    },
  })
}

onMounted(async () => {
  applicationsStore.restorePending()
  form.value = emptyForm(queryFromPage())
  await syncPending()
  await load()
})
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="content">
      <view class="hero">
        <text class="title">投递行动台</text>
        <text class="subtitle">记录真实投递、下一步和面试复盘。不会自动提交简历或访问招聘网站。</text>
      </view>

      <view class="summary-card">
        <view><text class="summary-number">{{ dueCount }}</text><text class="summary-label">条待跟进记录</text></view>
        <view v-if="applicationsStore.pendingCount" class="pending">
          <text>本机待同步 {{ applicationsStore.pendingCount }} 条</text>
          <button size="mini" @click="syncPending">重试同步</button>
        </view>
      </view>

      <view class="card">
        <view class="card-heading">
          <text>{{ form.id ? "编辑投递计划" : "新增投递计划" }}</text>
          <button v-if="form.id" size="mini" class="secondary" @click="resetForm">取消编辑</button>
        </view>
        <view class="field"><text>目标岗位</text><input v-model="form.roleName" placeholder="例如：数据工程师" /></view>
        <view class="field"><text>公司/组织</text><input v-model="form.company" placeholder="[待确认]" /></view>
        <view class="two-columns">
          <view class="field"><text>城市</text><input v-model="form.city" placeholder="上海" /></view>
          <view class="field"><text>投递来源</text><input v-model="form.source" placeholder="官网 / 内推 / 招聘会" /></view>
        </view>
        <view class="field">
          <text>当前状态</text>
          <picker :range="statusOptions.map((item) => item.label)" @change="selectStatus">
            <view class="picker">{{ statusOptions.find((item) => item.value === form.status)?.label }}</view>
          </picker>
        </view>
        <view class="two-columns">
          <view class="field"><text>投递日期</text><input v-model="form.appliedAt" placeholder="YYYY-MM-DD（可空）" /></view>
          <view class="field"><text>下一步日期</text><input v-model="form.nextActionAt" placeholder="YYYY-MM-DD（可空）" /></view>
        </view>
        <view class="two-columns">
          <view class="field"><text>联系人</text><input v-model="form.contactInfo" placeholder="姓名、电话或邮箱（可空）" /></view>
          <view class="field"><text>附件引用</text><input v-model="form.attachmentRef" placeholder="材料名称或本地引用（可空）" /></view>
        </view>
        <view class="field"><text>下次面试时间</text><input v-model="form.nextInterviewAt" placeholder="YYYY-MM-DDTHH:mm:ss+08:00（可空）" /></view>
        <view class="field"><text>面试复盘</text><textarea v-model="form.interviewNotes" placeholder="记录真实提问、表现和改进点" /></view>
        <view class="field"><text>备注</text><textarea v-model="form.notes" placeholder="例如：需要准备作品集" /></view>
        <view v-if="form.id" class="reminder-row">
          <input v-model="reminderAt" placeholder="提醒时间，例如 2026-08-25T09:30:00+08:00" />
          <button size="mini" class="secondary" @click="saveReminder">保存面试提醒</button>
        </view>
        <text v-if="form.draftId" class="linked-draft">已关联草稿：{{ form.draftId }}</text>
        <button class="primary" :loading="saving" @click="save">保存投递计划</button>
      </view>

      <view class="filter-row">
        <button
          v-for="item in statuses"
          :key="item.value"
          class="filter-chip"
          :class="{ active: selectedStatus === item.value }"
          @click="selectedStatus = item.value"
        >{{ item.label }}</button>
      </view>

      <view class="field interview-filter">
        <text>按面试日期筛选</text>
        <input v-model="interviewDate" placeholder="YYYY-MM-DD" />
      </view>

      <view v-if="upcomingInterviews.length" class="interview-panel">
        <text class="panel-title">面试日程</text>
        <text v-for="item in upcomingInterviews" :key="item.id" class="panel-item">{{ item.roleName }} · {{ item.company }} · {{ item.nextInterviewAt }}</text>
      </view>

      <text v-if="error" class="error">{{ error }}</text>
      <view v-else-if="loading" class="empty">正在加载投递记录…</view>
      <view v-else-if="!visibleApplications.length" class="empty">还没有投递计划。确认岗位与公司后，在上方手动保存第一条记录。</view>

      <view v-for="item in visibleApplications" :key="item.id" class="card record-card">
        <view class="record-top">
          <view><text class="record-role">{{ item.roleName }}</text><text class="record-company">{{ item.company }}</text></view>
          <text class="status">{{ statuses.find((status) => status.value === item.status)?.label }}</text>
        </view>
        <text v-if="item.city || item.source" class="detail">{{ [item.city, item.source].filter(Boolean).join(" · ") }}</text>
        <text v-if="item.appliedAt" class="detail">投递：{{ item.appliedAt }}</text>
        <text v-if="item.nextActionAt" class="next-action">下一步：{{ item.nextActionAt }}</text>
        <text v-if="item.nextInterviewAt" class="next-action">面试：{{ item.nextInterviewAt }}</text>
        <text v-if="item.contactInfo" class="detail">联系人：{{ item.contactInfo }}</text>
        <text v-if="item.attachmentRef" class="detail">附件：{{ item.attachmentRef }}</text>
        <text v-if="item.interviewNotes" class="detail">复盘：{{ item.interviewNotes }}</text>
        <text v-if="item.notes" class="detail">备注：{{ item.notes }}</text>
        <text v-if="item.draftId" class="linked-draft">关联草稿：{{ item.draftId }}</text>
        <view v-if="item.timeline?.length" class="timeline-list">
          <text v-for="event in item.timeline" :key="event.id" class="timeline-item">{{ event.occurredAt }} · {{ event.title }}<template v-if="event.description">：{{ event.description }}</template></text>
        </view>
        <view v-if="timelineDraft.applicationId === item.id" class="timeline-editor">
          <input v-model="timelineDraft.title" placeholder="时间线标题" />
          <input v-model="timelineDraft.occurredAt" placeholder="发生时间" />
          <textarea v-model="timelineDraft.description" placeholder="补充说明（可空）" />
          <button size="mini" class="secondary" @click="saveTimeline">添加时间线</button>
        </view>
        <view class="actions"><button size="mini" class="secondary" @click="edit(item)">编辑</button><button size="mini" class="secondary" @click="beginTimeline(item)">添加时间线</button><button size="mini" class="danger" @click="remove(item)">删除</button></view>
      </view>
    </view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; background: #f4f7fb; color: #1f2937; }.content { padding: 24rpx 24rpx 56rpx; }
.hero { padding: 30rpx 24rpx; background: linear-gradient(145deg,#e7f1ff,#f9fcff); border: 1rpx solid #d6e8ff; border-radius: 22rpx; }.title { display: block; font-size: 42rpx; font-weight: 700; }.subtitle { display: block; margin-top: 12rpx; color: #5f6f82; font-size: 24rpx; line-height: 1.65; }
.summary-card,.card { margin-top: 20rpx; padding: 24rpx; background: #fff; border: 1rpx solid #e5e6eb; border-radius: 18rpx; box-shadow: 0 8rpx 22rpx rgba(31,35,41,.04); }.summary-card { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; background: #eef8ff; border-color: #c7e5ff; }.summary-number,.summary-label { display: block; }.summary-number { color: #1677ff; font-size: 42rpx; font-weight: 700; }.summary-label { margin-top: 2rpx; color: #59728d; font-size: 23rpx; }.pending { display: flex; align-items: center; gap: 10rpx; color: #8a5a00; font-size: 22rpx; }.pending button { margin: 0; color: #1677ff; background: #fff; font-size: 21rpx; }
.card-heading,.record-top,.actions { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; }.card-heading { color: #1f2329; font-size: 30rpx; font-weight: 700; }.field { margin-top: 20rpx; }.field > text { display: block; margin-bottom: 10rpx; color: #4e5969; font-size: 24rpx; }.two-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 16rpx; } input,textarea,.picker { box-sizing: border-box; width: 100%; color: #1f2329; background: #f8fafc; border: 1rpx solid #dfe7f1; border-radius: 12rpx; font-size: 25rpx; } input,.picker { height: 76rpx; padding: 0 18rpx; line-height: 76rpx; } textarea { min-height: 120rpx; padding: 16rpx; line-height: 1.55; }
button { margin-top: 20rpx; border-radius: 12rpx; }.primary { color: #fff; background: #1677ff; }.secondary { margin-top: 0; color: #4e5969; background: #f2f3f5; }.danger { margin-top: 0; color: #d4380d; background: #fff1f0; }.linked-draft { display: block; margin-top: 12rpx; color: #86909c; font-size: 21rpx; }
.filter-row { display: flex; flex-wrap: wrap; gap: 10rpx; margin-top: 22rpx; }.filter-chip { margin: 0; padding: 8rpx 14rpx; color: #607286; background: #edf2f7; border-radius: 999rpx; font-size: 22rpx; }.filter-chip.active { color: #fff; background: #1677ff; }.empty,.error { display: block; margin-top: 20rpx; padding: 28rpx 22rpx; color: #86909c; background: #fff; border: 1rpx dashed #d9e0e8; border-radius: 16rpx; font-size: 24rpx; line-height: 1.6; text-align: center; }.error { color: #b3422a; background: #fff7f0; border-color: #ffd8bf; }
.record-card { padding: 22rpx; }.record-role,.record-company { display: block; }.record-role { color: #1f2329; font-size: 29rpx; font-weight: 700; }.record-company { margin-top: 6rpx; color: #86909c; font-size: 22rpx; }.status { flex-shrink: 0; padding: 7rpx 12rpx; color: #1677ff; background: #e8f3ff; border-radius: 999rpx; font-size: 21rpx; }.detail,.next-action { display: block; margin-top: 12rpx; color: #4e5969; font-size: 23rpx; line-height: 1.55; }.next-action { color: #a56727; }.actions { justify-content: flex-end; margin-top: 18rpx; }.actions button { min-width: 110rpx; }
.interview-filter { margin-top: 20rpx; }.interview-panel { margin-top: 20rpx; padding: 22rpx; background: #eef8ff; border: 1rpx solid #c7e5ff; border-radius: 16rpx; }.panel-title,.panel-item { display: block; }.panel-title { color: #245b99; font-size: 28rpx; font-weight: 700; }.panel-item { margin-top: 10rpx; color: #4e6682; font-size: 23rpx; line-height: 1.5; }.reminder-row { display: flex; align-items: center; gap: 12rpx; margin-top: 20rpx; }.reminder-row input { flex: 1; }.reminder-row button { flex-shrink: 0; }.timeline-list { margin-top: 16rpx; padding-top: 14rpx; border-top: 1rpx solid #e8edf3; }.timeline-item { display: block; margin-top: 8rpx; color: #5f6f82; font-size: 22rpx; line-height: 1.5; }.timeline-editor { display: grid; gap: 12rpx; margin-top: 16rpx; }.timeline-editor textarea { min-height: 90rpx; }.timeline-editor button { justify-self: start; margin-top: 0; }
@media (max-width: 360px) { .two-columns { grid-template-columns: 1fr; }.summary-card,.reminder-row { align-items: flex-start; flex-direction: column; }.reminder-row { gap: 10rpx; }.pending { align-items: flex-start; flex-direction: column; } }
</style>
