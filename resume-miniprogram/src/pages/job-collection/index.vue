<script setup lang="ts">
import { computed, onMounted, ref } from "vue"

import ExpandableText from "../../components/ExpandableText.vue"
import LoadingSpinner from "../../components/LoadingSpinner.vue"
import { useIncrementalList } from "../../composables/useIncrementalList"
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
import { runWithLoading } from "../../utils/async-state"

const resumeStore = useResumeStore()
const roleName = ref(resumeStore.activeJob?.roleName || resumeStore.draft.resume.job.targetRole || "")
const note = ref("")
const favorites = ref<FavoriteJob[]>([])
const {
  visibleItems: renderedItems,
  hasMore,
  showMore,
  reset: resetVisibleItems,
} = useIncrementalList(favorites)
const enabled = ref(false)
const matchFilter = ref("")
const lastNotifyAt = ref<string | null>(null)
const loading = ref(false)
const saving = ref(false)
const removingFavoriteId = ref("")
const subscriptionSaving = ref(false)
const error = ref("")
const selectedRole = computed(() => roleName.value.trim())
const currentFavorite = computed(() => favorites.value.find((item) => item.roleName === selectedRole.value))

async function load(): Promise<void> {
  error.value = ""
  try {
    const [items, subscribed] = await runWithLoading(
      (pending) => { loading.value = pending },
      () => Promise.all([listFavoriteJobs(), getJobMatchSubscriptionSettings()]),
    )
    favorites.value = items
    resetVisibleItems()
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
  if (saving.value || removingFavoriteId.value || subscriptionSaving.value) return
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
  if (removingFavoriteId.value || subscriptionSaving.value) return
  removingFavoriteId.value = id
  try {
    await deleteFavoriteJob(id)
    favorites.value = favorites.value.filter((item) => item.id !== id)
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to remove this job.")
  } finally {
    removingFavoriteId.value = ""
  }
}

async function updateSubscription(event: Event): Promise<void> {
  if (removingFavoriteId.value || subscriptionSaving.value) return
  const next = Boolean((event as unknown as { detail?: { value?: boolean } }).detail?.value)
  enabled.value = next
  subscriptionSaving.value = true
  try {
    const subscription = await setJobMatchSubscriptionSettings(next, matchFilter.value)
    enabled.value = subscription.enabled
    lastNotifyAt.value = subscription.lastNotifyAt
  } catch (reason) {
    enabled.value = !next
    error.value = toUserMessage(reason, "Unable to update the alert setting.")
  } finally {
    subscriptionSaving.value = false
  }
}

async function saveSubscriptionFilter(): Promise<void> {
  if (removingFavoriteId.value || subscriptionSaving.value) return
  subscriptionSaving.value = true
  try {
    const subscription = await setJobMatchSubscriptionSettings(enabled.value, matchFilter.value)
    enabled.value = subscription.enabled
    lastNotifyAt.value = subscription.lastNotifyAt
  } catch (reason) {
    error.value = toUserMessage(reason, "Unable to update the alert filter.")
  } finally {
    subscriptionSaving.value = false
  }
}

onMounted(() => { void load() })
</script>

<template>
  <scroll-view class="page progressive-scroll-page" scroll-y @scrolltolower="showMore">
    <view class="hero"><text class="eyebrow">JOB COLLECTION</text><text class="title">Saved job directions</text><text class="copy">Keep roles you want to revisit. External job matching and notifications are not connected in this development phase.</text></view>
    <view class="card">
      <text class="section-title">Save a role</text>
      <input v-model="roleName" placeholder="Data Engineer" />
      <textarea v-model="note" placeholder="Optional review note" />
      <button class="primary" :loading="saving" :disabled="saving" @click="toggleFavorite">{{ currentFavorite ? "Remove favorite" : "Save favorite" }}</button>
    </view>
    <view class="card subscription"><view><text class="section-title">Job matching alert</text><text class="copy">Save this preference now; actual alert delivery remains a mock.</text></view><switch class="subscription-switch" :class="{ 'subscription-switch--pending': subscriptionSaving }" :disabled="subscriptionSaving" :checked="enabled" color="#1677ff" @change="updateSubscription" /></view>
    <view class="card"><text class="section-title">Matching filter</text><input v-model="matchFilter" maxlength="200" placeholder="Shanghai, remote, data platform" /><button :loading="subscriptionSaving" :disabled="subscriptionSaving" @click="saveSubscriptionFilter">Save filter</button><text v-if="lastNotifyAt" class="copy">Last alert: {{ lastNotifyAt }}</text></view>
      <text v-if="error" class="ui-error-tip">{{ error }}</text>
    <view v-if="loading" class="notice"><LoadingSpinner size="sm" label="Loading saved jobs..." /><text>Loading saved jobs...</text></view>
    <view v-for="item in renderedItems" :key="item.id" class="favorite-card ui-long-list-item"><view><ExpandableText class="role" :text="item.roleName" :lines="1" :expand-at="18" label="岗位名称" /><text v-if="item.note" class="copy">{{ item.note }}</text></view><button size="mini" :loading="removingFavoriteId === item.id" :disabled="Boolean(removingFavoriteId)" @click="removeFavorite(item.id)">Remove</button></view>
    <text v-if="hasMore" class="progressive-list-hint">继续下滑显示更多</text>
    <view v-if="!loading && !favorites.length" class="empty-state"><view class="empty-illustration"><view></view><view></view><view></view></view><text>No saved jobs yet</text></view>
  </scroll-view>
</template>

<style scoped>
.subscription-switch { transition: transform var(--ui-motion-fast) var(--ui-motion-ease), opacity var(--ui-motion-fast) var(--ui-motion-ease); }.subscription-switch--pending { opacity: .65; transform: scale(.96); }
</style>
