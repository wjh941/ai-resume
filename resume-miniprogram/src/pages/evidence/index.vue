<script setup lang="ts">
import { onMounted, ref } from "vue"

import { useIncrementalList } from "../../composables/useIncrementalList"
import {
  deleteEvidence,
  listEvidence,
  saveEvidence,
} from "../../services/evidence-api"
import LoadingSpinner from "../../components/LoadingSpinner.vue"
import { getClientId } from "../../stores/session"
import { showErrorToast } from "../../utils/error-feedback"
import type {
  EvidenceKind,
  ResumeEvidence,
  ResumeEvidenceInput,
} from "../../types/evidence"

const kindOptions: Array<{ value: EvidenceKind; label: string }> = [
  { value: "coursework", label: "课程/作业" },
  { value: "project", label: "项目经历" },
  { value: "activity", label: "社团/校园活动" },
  { value: "internship", label: "实习经历" },
  { value: "employment", label: "工作经历" },
]

const evidence = ref<ResumeEvidence[]>([])
const {
  visibleItems: renderedItems,
  hasMore,
  showMore,
  reset: resetVisibleItems,
} = useIncrementalList(evidence)
const loading = ref(false)
const saving = ref(false)
const pendingDeleteId = ref<string | null>(null)
const form = ref<ResumeEvidenceInput>(emptyForm())

function emptyForm(): ResumeEvidenceInput {
  return {
    clientId: getClientId(),
    kind: "project",
    title: "",
    context: "",
    actions: "",
    outcome: "",
    proofNote: "",
    verified: false,
  }
}

function selectKind(event: Event) {
  const index = Number((event as unknown as { detail?: { value?: string } }).detail?.value)
  if (kindOptions[index]) form.value.kind = kindOptions[index].value
}

async function load() {
  loading.value = true
  try {
    evidence.value = await listEvidence(getClientId())
    resetVisibleItems()
  } catch (reason) {
    showErrorToast(reason instanceof Error ? reason.message : "经历证据加载失败")
  } finally {
    loading.value = false
  }
}

async function save() {
  if (saving.value) return
  if (!form.value.title.trim() || !form.value.actions.trim()) {
    showErrorToast("请填写经历标题和真实行动")
    return
  }
  saving.value = true
  try {
    const saved = await saveEvidence({ ...form.value, clientId: getClientId() })
    const index = evidence.value.findIndex((item) => item.id === saved.id)
    if (index >= 0) evidence.value.splice(index, 1, saved)
    else evidence.value.unshift(saved)
    form.value = emptyForm()
    uni.showToast({ title: "经历证据已保存", icon: "success" })
  } catch (reason) {
    showErrorToast(reason instanceof Error ? reason.message : "经历证据保存失败")
  } finally {
    saving.value = false
  }
}

function edit(item: ResumeEvidence) {
  form.value = {
    id: item.id,
    clientId: item.clientId,
    kind: item.kind,
    title: item.title,
    context: item.context,
    actions: item.actions,
    outcome: item.outcome,
    proofNote: item.proofNote,
    verified: item.verified,
  }
  uni.pageScrollTo({ scrollTop: 0, duration: 180 })
}

async function remove(item: ResumeEvidence) {
  if (pendingDeleteId.value) return
  pendingDeleteId.value = item.id
  try {
    await deleteEvidence(getClientId(), item.id)
    evidence.value = evidence.value.filter((current) => current.id !== item.id)
    if (form.value.id === item.id) form.value = emptyForm()
    uni.showToast({ title: "经历证据已删除", icon: "success" })
  } catch (reason) {
    showErrorToast(reason instanceof Error ? reason.message : "删除失败")
  } finally {
    pendingDeleteId.value = null
  }
}

function resetForm() {
  form.value = emptyForm()
}

onMounted(() => {
  void load()
})
</script>

<template>
  <scroll-view class="page progressive-scroll-page" scroll-y @scrolltolower="showMore">
    <view class="content">
      <view class="hero">
        <text class="eyebrow">FACT-BASED RESUME</text>
        <text class="title">经历证据库</text>
        <text class="subtitle">记录你真实完成过的课程、项目和实践。AI 只会基于这些内容生成草案，不会补造公司、日期、数据或成果。</text>
      </view>

      <view class="notice">
        <text class="notice-title">导出前请确认</text>
        <text class="notice-text">没有真实成果或可核验证据时，保留“待确认”即可；不要为简历虚构量化结果。</text>
      </view>

      <view class="card">
        <view class="card-heading">
          <text>{{ form.id ? "编辑经历证据" : "新增真实经历" }}</text>
          <button v-if="form.id" size="mini" class="secondary" @click="resetForm">取消编辑</button>
        </view>

        <view class="field">
          <text>经历类型</text>
          <picker :range="kindOptions.map((item) => item.label)" @change="selectKind">
            <view class="picker">{{ kindOptions.find((item) => item.value === form.kind)?.label }}</view>
          </picker>
        </view>
        <view class="field"><text>标题</text><input v-model="form.title" placeholder="例如：数据仓库课程项目" /></view>
        <view class="field"><text>场景/背景</text><textarea v-model="form.context" placeholder="课程、团队、项目背景或任务目标" /></view>
        <view class="field"><text>你的真实行动</text><textarea v-model="form.actions" placeholder="写明你亲自完成的分析、开发、协作或交付动作" /></view>
        <view class="field"><text>真实成果</text><textarea v-model="form.outcome" placeholder="未知可以留空，不填写虚构数据" /></view>
        <view class="field"><text>证据说明</text><textarea v-model="form.proofNote" placeholder="例如：代码仓库、作品、截图、报告或证书" /></view>
        <view class="verified-row">
          <view><text class="verified-title">我确认以上信息真实准确</text><text class="verified-hint">确认后会优先用于岗位相关建议。</text></view>
          <switch :checked="form.verified" color="#1677ff" @change="form.verified = $event.detail.value" />
        </view>
        <button class="primary" :loading="saving" :disabled="saving" @click="save">{{ form.id ? "保存修改" : "保存经历证据" }}</button>
      </view>

      <view class="list-heading">
        <text>已保存经历</text>
        <text>{{ loading ? "加载中" : `${evidence.length} 条` }}</text>
      </view>
      <LoadingSpinner v-if="loading" size="sm" label="正在加载经历证据" />
      <view v-if="!loading && !evidence.length" class="empty">
        <text>先录入一条真实经历，后续可按目标岗位生成可确认的简历草案。</text>
      </view>
      <view v-for="item in renderedItems" :key="item.id" class="card evidence-card ui-long-list-item">
        <view class="evidence-top">
          <view>
            <text class="evidence-title">{{ item.title }}</text>
            <text class="evidence-kind">{{ kindOptions.find((option) => option.value === item.kind)?.label }}</text>
          </view>
          <text class="status" :class="{ verified: item.verified }">{{ item.verified ? "已确认" : "待确认" }}</text>
        </view>
        <text v-if="item.context" class="detail">场景：{{ item.context }}</text>
        <text class="detail">行动：{{ item.actions }}</text>
        <text v-if="item.outcome" class="detail">成果：{{ item.outcome }}</text>
        <text v-if="item.proofNote" class="proof">证据：{{ item.proofNote }}</text>
        <view class="actions">
          <button size="mini" class="secondary" @click="edit(item)">编辑</button>
          <button size="mini" class="danger" :loading="pendingDeleteId === item.id" :disabled="Boolean(pendingDeleteId)" @click="remove(item)">删除</button>
        </view>
      </view>
      <text v-if="hasMore" class="progressive-list-hint">继续下滑显示更多</text>
    </view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; background: #f7f8fa; color: #1f2329; }
.content { padding: 24rpx 24rpx 56rpx; }
.hero { padding: 32rpx 24rpx; background: linear-gradient(145deg, #e8f3ff, #f9fcff); border: 1rpx solid #d6e8ff; border-radius: 22rpx; }
.eyebrow { display: block; color: #1677ff; font-size: 21rpx; font-weight: 700; letter-spacing: 1rpx; }
.title { display: block; margin-top: 10rpx; font-size: 42rpx; font-weight: 700; }
.subtitle { display: block; margin-top: 12rpx; color: #5f6f82; font-size: 25rpx; line-height: 1.65; }
.notice, .card { margin-top: 20rpx; padding: 24rpx; background: #fff; border: 1rpx solid #e5e6eb; border-radius: 18rpx; box-shadow: 0 8rpx 22rpx rgba(31, 35, 41, .04); }
.notice { background: #fffbe8; border-color: #ffe7a8; }.notice-title, .notice-text { display: block; }.notice-title { color: #8a5a00; font-size: 27rpx; font-weight: 700; }.notice-text { margin-top: 8rpx; color: #7d6541; font-size: 23rpx; line-height: 1.55; }
.card-heading, .evidence-top, .list-heading, .verified-row, .actions { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; }
.card-heading, .list-heading { font-size: 30rpx; font-weight: 700; }.list-heading { margin: 28rpx 4rpx 0; color: #1f2329; }.list-heading text:last-child { color: #86909c; font-size: 23rpx; font-weight: 400; }
.field { margin-top: 20rpx; }.field > text { display: block; margin-bottom: 10rpx; color: #4e5969; font-size: 24rpx; }
input, textarea, .picker { box-sizing: border-box; width: 100%; color: #1f2329; background: #f8fafc; border: 1rpx solid #dfe7f1; border-radius: 12rpx; font-size: 26rpx; }
input, .picker { height: 78rpx; padding: 0 18rpx; line-height: 78rpx; } textarea { min-height: 132rpx; padding: 16rpx; line-height: 1.55; }
.verified-row { margin-top: 22rpx; padding: 18rpx; background: #f7faff; border-radius: 14rpx; }.verified-title, .verified-hint { display: block; }.verified-title { color: #334155; font-size: 25rpx; font-weight: 600; }.verified-hint { margin-top: 5rpx; color: #86909c; font-size: 21rpx; }
button { margin-top: 20rpx; border-radius: 12rpx; }.primary { color: #fff; background: #1677ff; }.secondary { margin-top: 0; color: #4e5969; background: #f2f3f5; }.danger { margin-top: 0; color: #d4380d; background: #fff1f0; }
.empty { margin-top: 20rpx; padding: 30rpx 24rpx; color: #86909c; background: #fff; border: 1rpx dashed #d9e0e8; border-radius: 16rpx; font-size: 25rpx; line-height: 1.6; text-align: center; }
.evidence-card { padding: 22rpx; }.evidence-title { display: block; color: #1f2329; font-size: 29rpx; font-weight: 700; }.evidence-kind { display: block; margin-top: 6rpx; color: #86909c; font-size: 21rpx; }.status { flex-shrink: 0; padding: 7rpx 12rpx; color: #c2410c; background: #fff7ed; border-radius: 999rpx; font-size: 21rpx; }.status.verified { color: #1677ff; background: #e8f3ff; }
.detail, .proof { display: block; margin-top: 13rpx; color: #4e5969; font-size: 24rpx; line-height: 1.55; }.proof { color: #75869a; }.actions { justify-content: flex-end; margin-top: 18rpx; }.actions button { min-width: 110rpx; }
</style>
