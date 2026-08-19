<script setup lang="ts">
import { computed, onMounted, ref } from "vue"

import {
  deleteFavoriteJob,
  getJobMatchSubscriptionSettings,
  listFavoriteJobs,
  saveFavoriteJob,
  setJobMatchSubscriptionSettings,
  type FavoriteJob,
} from "../../services/job-collection-api"
import { toUserMessage } from "../../services/http"
import { useResumeStore } from "../../stores/resume"

const resumeStore = useResumeStore()
const roleName = ref(resumeStore.activeJob?.roleName || resumeStore.draft.resume.job.targetRole || "")
const note = ref("")
const favorites = ref<FavoriteJob[]>([])
const enabled = ref(false)
const matchFilter = ref("")
const lastNotifyAt = ref<string | null>(null)
const loading = ref(false)
const saving = ref(false)
const error = ref("")
const selectedRole = computed(() => roleName.value.trim())
const currentFavorite = computed(() => favorites.value.find((item) => item.roleName === selectedRole.value))

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    const [items, subscribed] = await Promise.all([listFavoriteJobs(), getJobMatchSubscriptionSettings()])
    favorites.value = items
    enabled.value = subscribed.enabled
    matchFilter.value = subscribed.matchFilter
    lastNotifyAt.value = subscribed.lastNotifyAt
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to load saved jobs.")
  } finally {
    loading.value = false
  }
}

async function toggleFavorite(): Promise<void> {
  if (!selectedRole.value) {
    error.value = "Enter a job role to save it."
    return
  }
  saving.value = true
  error.value = ""
  try {
    if (currentFavorite.value) {
      await deleteFavoriteJob(currentFavorite.value.id)
      favorites.value = favorites.value.filter((item) => item.id !== currentFavorite.value?.id)
      return
    }
    const saved = await saveFavoriteJob(selectedRole.value, note.value)
    const index = favorites.value.findIndex((item) => item.id === saved.id)
    if (index >= 0) favorites.value.splice(index, 1, saved)
    else favorites.value.unshift(saved)
    note.value = ""
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to save this job.")
  } finally {
    saving.value = false
  }
}

async function removeFavorite(id: string): Promise<void> {
  try {
    await deleteFavoriteJob(id)
    favorites.value = favorites.value.filter((item) => item.id !== id)
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to remove this job.")
  }
}

async function updateSubscription(event: Event): Promise<void> {
  const next = Boolean((event as unknown as { detail?: { value?: boolean } }).detail?.value)
  enabled.value = next
  try {
    const subscription = await setJobMatchSubscriptionSettings(next, matchFilter.value)
    enabled.value = subscription.enabled
    lastNotifyAt.value = subscription.lastNotifyAt
  } catch (reason) {
    enabled.value = !next
    error.value = toUserMessage(reason, "Unable to update the alert setting.")
  }
}

async function saveSubscriptionFilter(): Promise<void> {
  try {
    const subscription = await setJobMatchSubscriptionSettings(enabled.value, matchFilter.value)
    enabled.value = subscription.enabled
    lastNotifyAt.value = subscription.lastNotifyAt
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to update the alert filter.")
  }
}

onMounted(() => { void load() })
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="hero"><text class="eyebrow">JOB COLLECTION</text><text class="title">Saved job directions</text><text class="copy">Keep roles you want to revisit. External job matching and notifications are not connected in this development phase.</text></view>
    <view class="card">
      <text class="section-title">Save a role</text>
      <input v-model="roleName" placeholder="Data Engineer" />
      <textarea v-model="note" placeholder="Optional review note" />
      <button class="primary" :loading="saving" @click="toggleFavorite">{{ currentFavorite ? "Remove favorite" : "Save favorite" }}</button>
    </view>
    <view class="card subscription"><view><text class="section-title">Job matching alert</text><text class="copy">Save this preference now; actual alert delivery remains a mock.</text></view><switch :checked="enabled" color="#1677ff" @change="updateSubscription" /></view>
    <view class="card"><text class="section-title">Matching filter</text><input v-model="matchFilter" maxlength="200" placeholder="Shanghai, remote, data platform" /><button @click="saveSubscriptionFilter">Save filter</button><text v-if="lastNotifyAt" class="copy">Last alert: {{ lastNotifyAt }}</text></view>
    <text v-if="error" class="error">{{ error }}</text>
    <text v-if="loading" class="notice">Loading saved jobs...</text>
    <view v-for="item in favorites" :key="item.id" class="favorite-card"><view><text class="role">{{ item.roleName }}</text><text v-if="item.note" class="copy">{{ item.note }}</text></view><button size="mini" @click="removeFavorite(item.id)">Remove</button></view>
    <view v-if="!loading && !favorites.length" class="empty-state"><view class="empty-illustration"><view></view><view></view><view></view></view><text>No saved jobs yet</text></view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; box-sizing: border-box; padding: 28rpx; background: #f4f7fb; }.hero,.card,.favorite-card { padding: 26rpx; background: #fff; border: 1rpx solid #e1eaf4; border-radius: 18rpx; box-shadow: 0 8rpx 22rpx rgba(35, 78, 130, .06); }.eyebrow,.title,.copy,.section-title,.error,.notice,.role,.empty-state > text { display: block; }.eyebrow { color: #1677ff; font-size: 21rpx; font-weight: 700; }.title { margin-top: 10rpx; color: #1f2937; font-size: 38rpx; font-weight: 700; }.copy { margin-top: 9rpx; color: #64748b; font-size: 23rpx; line-height: 1.55; }.card { margin-top: 20rpx; }.section-title { color: #334155; font-size: 29rpx; font-weight: 700; }.card input,.card textarea { width: 100%; box-sizing: border-box; margin-top: 16rpx; padding: 16rpx; background: #f8fafc; border: 1rpx solid #dfe7f1; border-radius: 12rpx; font-size: 26rpx; }.card input { min-height: 76rpx; }.card textarea { min-height: 120rpx; }.primary { margin-top: 16rpx; color: #fff; background: #1677ff; }.subscription,.favorite-card { display: flex; align-items: center; justify-content: space-between; gap: 18rpx; }.favorite-card { margin-top: 16rpx; }.favorite-card button { flex-shrink: 0; margin: 0; color: #245b99; background: #edf6ff; font-size: 22rpx; }.role { color: #1f2937; font-size: 29rpx; font-weight: 700; }.error,.notice { margin-top: 18rpx; font-size: 24rpx; }.error { color: #c2410c; }.notice { color: #64748b; text-align: center; }.empty-state { margin-top: 36rpx; text-align: center; color: #64748b; font-size: 25rpx; }.empty-illustration { display: flex; flex-direction: column; gap: 8rpx; width: 110rpx; margin: 0 auto 18rpx; padding: 18rpx; background: #eef6ff; border: 1rpx solid #d4e8ff; border-radius: 16rpx; }.empty-illustration view { height: 9rpx; background: #9fc8f7; border-radius: 999rpx; }.empty-illustration view:nth-child(2) { width: 75%; }.empty-illustration view:nth-child(3) { width: 50%; }
</style>
