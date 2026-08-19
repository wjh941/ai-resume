<script setup lang="ts">
import { onMounted, ref } from "vue"

import {
  copyDraft,
  deleteDraft,
  getDraft,
  listDrafts,
  toResumeDraft,
  type DraftRecord,
} from "../../services/drafts-api"
import { useResumeStore } from "../../stores/resume"
import { getClientId } from "../../stores/session"

const resumeStore = useResumeStore()
const drafts = ref<DraftRecord[]>([])
const loading = ref(false)
const error = ref("")

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    drafts.value = await listDrafts(getClientId())
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to load drafts"
  } finally {
    loading.value = false
  }
}

async function openDraft(item: DraftRecord): Promise<void> {
  try {
    const draft = await getDraft(getClientId(), item.id)
    resumeStore.draft = toResumeDraft(draft)
    resumeStore.activeJob = draft.jobIntelligence
    resumeStore.checkpoint()
    uni.navigateTo({ url: "/pages/resume-editor/index" })
  } catch (reason) {
    uni.showToast({ title: reason instanceof Error ? reason.message : "Unable to open draft", icon: "none" })
  }
}

async function copy(item: DraftRecord): Promise<void> {
  try {
    const copied = await copyDraft(getClientId(), item.id)
    drafts.value.unshift(copied)
    uni.showToast({ title: "Draft copied", icon: "success" })
  } catch (reason) {
    uni.showToast({ title: reason instanceof Error ? reason.message : "Unable to copy draft", icon: "none" })
  }
}

function remove(item: DraftRecord): void {
  uni.showModal({
    title: "Delete draft",
    content: `Delete ${item.jobTitle || "this draft"}?`,
    success: async (result) => {
      if (!result.confirm) return
      try {
        await deleteDraft(getClientId(), item.id)
        drafts.value = drafts.value.filter((draft) => draft.id !== item.id)
        uni.showToast({ title: "Draft deleted", icon: "success" })
      } catch (reason) {
        uni.showToast({ title: reason instanceof Error ? reason.message : "Unable to delete draft", icon: "none" })
      }
    },
  })
}

function createTrackerPrefill(item: DraftRecord): void {
  const params = new URLSearchParams({ draftId: item.id })
  const roleName = item.jobTitle || item.resume.job.targetRole
  if (roleName) params.set("roleName", roleName)
  if (item.resume.basic.city) params.set("city", item.resume.basic.city)
  uni.navigateTo({ url: `/pages/applications/index?${params}` })
}

onMounted(load)
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="heading-row">
      <view><text class="title">Drafts</text><text class="subtitle">Open, copy, or prepare a tracker entry.</text></view>
      <button size="mini" @click="load">Refresh</button>
    </view>
    <text v-if="loading" class="notice">Loading drafts...</text>
    <text v-else-if="error" class="error">{{ error }}</text>
    <view v-else-if="!drafts.length" class="empty-state">
      <view class="empty-illustration" aria-hidden="true"><view></view><view></view><view></view></view>
      <text class="empty-title">No resume drafts yet</text>
      <text class="notice">Your saved resume history will appear here.</text>
    </view>
    <view v-for="item in drafts" :key="item.id" class="draft">
      <text class="draft-title">{{ item.jobTitle || item.resume.job.targetRole || "Untitled draft" }}</text>
      <text class="draft-meta">Updated {{ item.updatedAt }}</text>
      <view class="actions">
        <button size="mini" class="primary" @click="openDraft(item)">Open</button>
        <button size="mini" @click="copy(item)">Copy</button>
        <button size="mini" @click="createTrackerPrefill(item)">Tracker</button>
        <button size="mini" class="danger" @click="remove(item)">Delete</button>
      </view>
    </view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; box-sizing: border-box; padding: 28rpx; background: #f7f8fa; color: #1f2329; }
.heading-row { display: flex; align-items: center; justify-content: space-between; gap: 20rpx; }
.title,.subtitle,.draft-title,.draft-meta,.notice,.error { display: block; }.title { font-size: 40rpx; font-weight: 700; }.subtitle,.draft-meta,.notice { margin-top: 8rpx; color: #86909c; font-size: 24rpx; }.notice,.error { margin-top: 32rpx; text-align: center; }.error { color: #d4380d; }
.draft { margin-top: 20rpx; padding: 24rpx; background: #fff; border: 1rpx solid #e5e6eb; border-radius: 12rpx; }.draft-title { font-size: 30rpx; font-weight: 600; }.actions { display: flex; flex-wrap: wrap; gap: 12rpx; margin-top: 20rpx; }.actions button { margin: 0; font-size: 23rpx; }.primary { color: #fff; background: #1677ff; }.danger { color: #d4380d; background: #fff1f0; }.empty-state { margin-top: 42rpx; padding: 34rpx 24rpx; text-align: center; }.empty-illustration { display: flex; flex-direction: column; gap: 8rpx; width: 116rpx; margin: 0 auto 20rpx; padding: 20rpx; background: #eef6ff; border: 1rpx solid #d4e8ff; border-radius: 18rpx; }.empty-illustration view { height: 9rpx; background: #9fc8f7; border-radius: 999rpx; }.empty-illustration view:nth-child(2) { width: 76%; }.empty-illustration view:nth-child(3) { width: 54%; }.empty-title { display: block; color: #1f3e61; font-size: 29rpx; font-weight: 700; }
</style>
