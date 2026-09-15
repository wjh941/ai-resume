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
import { defaultCapabilities, getCapabilities, isCapabilityEnabled, type Capabilities } from "../../services/capability-api"
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
const capabilities = ref<Capabilities>(defaultCapabilities())
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
    error.value = toUserMessage(reason, "无法加载已收藏岗位，请稍后重试。")
  } finally {
    loading.value = false
  }
}

async function toggleFavorite(): Promise<void> {
  if (saving.value || removingFavoriteId.value || subscriptionSaving.value) return
  if (!selectedRole.value) {
    error.value = "请输入岗位名称后再收藏。"
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
    error.value = toUserMessage(reason, "岗位收藏失败，请稍后重试。")
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
    error.value = toUserMessage(reason, "取消收藏失败，请稍后重试。")
  } finally {
    removingFavoriteId.value = ""
  }
}

async function updateSubscription(event: Event): Promise<void> {
  if (removingFavoriteId.value || subscriptionSaving.value) return
  if (!isCapabilityEnabled(capabilities.value, "jobMatching")) {
    error.value = capabilities.value.jobMatching.notice
    return
  }
  const next = Boolean((event as unknown as { detail?: { value?: boolean } }).detail?.value)
  enabled.value = next
  subscriptionSaving.value = true
  try {
    const subscription = await setJobMatchSubscriptionSettings(next, matchFilter.value)
    enabled.value = subscription.enabled
    lastNotifyAt.value = subscription.lastNotifyAt
  } catch (reason) {
    enabled.value = !next
    error.value = toUserMessage(reason, "提醒设置更新失败，请稍后重试。")
  } finally {
    subscriptionSaving.value = false
  }
}

async function saveSubscriptionFilter(): Promise<void> {
  if (removingFavoriteId.value || subscriptionSaving.value) return
  if (!isCapabilityEnabled(capabilities.value, "jobMatching")) {
    error.value = capabilities.value.jobMatching.notice
    return
  }
  subscriptionSaving.value = true
  try {
    const subscription = await setJobMatchSubscriptionSettings(enabled.value, matchFilter.value)
    enabled.value = subscription.enabled
    lastNotifyAt.value = subscription.lastNotifyAt
  } catch (reason) {
    error.value = toUserMessage(reason, "提醒筛选条件更新失败，请稍后重试。")
  } finally {
    subscriptionSaving.value = false
  }
}

onMounted(async () => {
  void load()
  capabilities.value = await getCapabilities()
})
</script>

<template>
  <scroll-view class="page progressive-scroll-page" scroll-y @scrolltolower="showMore">
    <view class="hero"><text class="eyebrow">岗位收藏</text><text class="title">保存值得再次查看的岗位</text><text class="copy">集中管理目标岗位。外部岗位匹配与通知服务尚未接入。</text></view>
    <view class="card">
      <text class="section-title">收藏岗位</text>
      <input v-model="roleName" placeholder="例如：数据工程师" />
      <textarea v-model="note" placeholder="可添加复盘备注" />
      <button class="primary" :loading="saving" :disabled="saving" @click="toggleFavorite">{{ currentFavorite ? "取消收藏" : "收藏岗位" }}</button>
    </view>
    <view class="card subscription"><view><text class="section-title">岗位匹配提醒</text><text class="copy">{{ capabilities.jobMatching.notice }}</text></view><switch class="subscription-switch" :class="{ 'subscription-switch--pending': subscriptionSaving }" :disabled="subscriptionSaving || !capabilities.jobMatching.enabled" :checked="enabled" color="#1677ff" @change="updateSubscription" /></view>
    <view class="card"><text class="section-title">匹配筛选条件</text><input v-model="matchFilter" maxlength="200" placeholder="上海、远程、数据平台" /><button :loading="subscriptionSaving" :disabled="subscriptionSaving || !capabilities.jobMatching.enabled" @click="saveSubscriptionFilter">保存筛选条件</button><text v-if="lastNotifyAt" class="copy">上次提醒：{{ lastNotifyAt }}</text></view>
      <text v-if="error" class="ui-error-tip" role="alert">{{ error }}</text>
    <view v-if="loading" class="notice"><LoadingSpinner size="sm" label="正在加载已收藏岗位" /><text>正在加载已收藏岗位</text></view>
    <view v-for="item in renderedItems" :key="item.id" class="favorite-card ui-long-list-item"><view><ExpandableText class="role" :text="item.roleName" :lines="1" :expand-at="18" label="岗位名称" /><text v-if="item.note" class="copy">{{ item.note }}</text></view><button size="mini" :loading="removingFavoriteId === item.id" :disabled="Boolean(removingFavoriteId)" @click="removeFavorite(item.id)">取消收藏</button></view>
    <text v-if="hasMore" class="progressive-list-hint">继续下滑显示更多</text>
    <view v-if="!loading && !favorites.length" class="empty-state"><view class="empty-illustration" aria-hidden="true"><view></view><view></view><view></view></view><text>还没有收藏岗位</text></view>
  </scroll-view>
</template>

<style scoped>
.subscription-switch { transition: transform var(--ui-motion-fast) var(--ui-motion-ease), opacity var(--ui-motion-fast) var(--ui-motion-ease); }.subscription-switch--pending { opacity: .65; transform: scale(.96); }
 .page { min-height: 100dvh; box-sizing: border-box; padding: 28rpx; background: #f7f8fa; color: #1f2329; }
 .hero { margin-bottom: 20rpx; padding: 32rpx 24rpx; background: linear-gradient(145deg, #eaf3ff, #f8fbff); border: 1rpx solid #d8eaff; border-radius: 20rpx; }
 .eyebrow { display: block; color: #50739b; font-size: 21rpx; letter-spacing: 1rpx; }.title { display: block; margin-top: 10rpx; color: #1f3e61; font-size: 40rpx; font-weight: 700; line-height: 1.25; }.copy { display: block; margin-top: 8rpx; color: #64748b; font-size: 23rpx; line-height: 1.55; }
 .card,.favorite-card,.empty-state { box-sizing: border-box; margin-top: 20rpx; padding: 24rpx; background: #fff; border: 1rpx solid #e7edf5; border-radius: 16rpx; box-shadow: 0 8rpx 24rpx rgba(35,78,130,.06); }.section-title { display: block; color: #243b53; font-size: 29rpx; font-weight: 700; }.card input,.card textarea { box-sizing: border-box; width: 100%; margin-top: 14rpx; padding: 16rpx; background: #f8fafc; border: 1rpx solid #dfe7f1; border-radius: 10rpx; font-size: 25rpx; }.card textarea { min-height: 120rpx; }.card button { margin-top: 16rpx; }.primary { color: #fff; background: #0f63ce; }.subscription { display: flex; align-items: center; justify-content: space-between; gap: 20rpx; }.subscription > view { min-width: 0; }.subscription-switch { flex: 0 0 auto; }.favorite-card { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; }.favorite-card > view { min-width: 0; }.role { display: block; color: #1f3e61; font-size: 28rpx; font-weight: 650; }.favorite-card button { flex: 0 0 auto; margin: 0; }.notice { display: flex; min-height: 120rpx; align-items: center; justify-content: center; gap: 12rpx; color: #64748b; }.empty-state { padding: 64rpx 24rpx; text-align: center; }.empty-illustration { display: flex; flex-direction: column; gap: 8rpx; width: 120rpx; margin: 0 auto 22rpx; padding: 20rpx; background: #eef6ff; border: 1rpx solid #d4e8ff; border-radius: 16rpx; }.empty-illustration view { height: 10rpx; background: #9fc8f7; border-radius: 999rpx; }.empty-illustration view:nth-child(2) { width: 78%; }.empty-illustration view:nth-child(3) { width: 55%; }.empty-state text { color: #64748b; font-size: 25rpx; }
 @media (max-width: 480px) { .page { padding: 20rpx; }.subscription { align-items: flex-start; }.favorite-card { align-items: flex-start; } }
 @media (prefers-reduced-motion: reduce) { .subscription-switch { transition: none; }.subscription-switch--pending { transform: none; } }
</style>
