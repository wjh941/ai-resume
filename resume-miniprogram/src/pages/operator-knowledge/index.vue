<script setup lang="ts">
import { onMounted, ref } from "vue"

import LoadingSpinner from "../../components/LoadingSpinner.vue"
import { createOperatorKnowledge, listOperatorKnowledge, listOperatorKnowledgeVersions, restoreOperatorKnowledgeVersion, updateOperatorKnowledge, type OperatorKnowledgeItem, type OperatorKnowledgeVersion } from "../../services/operator-api"
import { toUserMessage } from "../../services/http"
import { getAuthUser } from "../../stores/session"

const statusOptions: OperatorKnowledgeItem["status"][] = ["active", "offline", "invalid"]
const statusLabels: Record<OperatorKnowledgeItem["status"], string> = { active: "已启用", offline: "已下线", invalid: "标记无效" }
const items = ref<OperatorKnowledgeItem[]>([])
const versions = ref<OperatorKnowledgeVersion[]>([])
const selectedItemId = ref("")
const title = ref("")
const content = ref("")
const status = ref<OperatorKnowledgeItem["status"]>("active")
const loading = ref(false)
const saving = ref(false)
const versionsLoading = ref("")
const restoringVersion = ref<number | null>(null)
const error = ref("")

function clearForm(): void {
  selectedItemId.value = ""
  title.value = ""
  content.value = ""
  status.value = "active"
  versions.value = []
}

async function loadItems(): Promise<void> {
  loading.value = true
  error.value = ""
  try { items.value = await listOperatorKnowledge() } catch (reason) { error.value = toUserMessage(reason, "无法加载运营知识库，请稍后重试。") } finally { loading.value = false }
}

async function editItem(item: OperatorKnowledgeItem): Promise<void> {
  if (versionsLoading.value || restoringVersion.value !== null) return
  selectedItemId.value = item.id
  title.value = item.title
  content.value = item.content
  status.value = item.status
  versionsLoading.value = item.id
  try { versions.value = await listOperatorKnowledgeVersions(item.id) } catch (reason) { error.value = toUserMessage(reason, "无法加载历史版本，请稍后重试。") } finally { versionsLoading.value = "" }
}

function changeStatus(event: { detail: { value: string } }): void {
  status.value = statusOptions[Number(event.detail.value)] || "active"
}

async function saveItem(): Promise<void> {
  if (saving.value) return
  if (!title.value.trim() || !content.value.trim()) { error.value = "请填写知识标题和内容。"; return }
  saving.value = true
  error.value = ""
  try {
    const item = selectedItemId.value
      ? await updateOperatorKnowledge(selectedItemId.value, { title: title.value, content: content.value, status: status.value })
      : await createOperatorKnowledge({ title: title.value, content: content.value, status: status.value })
    await loadItems()
    await editItem(item)
    uni.showToast({ title: "知识内容已保存", icon: "success" })
  } catch (reason) { error.value = toUserMessage(reason, "保存知识内容失败，请稍后重试。") } finally { saving.value = false }
}

function restoreVersion(version: OperatorKnowledgeVersion): void {
  if (!selectedItemId.value || restoringVersion.value !== null || versionsLoading.value) return
  uni.showModal({ title: "恢复历史版本", content: "恢复后会生成一个新的当前版本，原有版本记录不会被删除。", success: async (result) => {
    if (!result.confirm || !selectedItemId.value) return
    restoringVersion.value = version.version
    try {
      const item = await restoreOperatorKnowledgeVersion(selectedItemId.value, version.version)
      await loadItems()
      await editItem(item)
      uni.showToast({ title: "已恢复历史版本", icon: "success" })
    } catch (reason) { error.value = toUserMessage(reason, "恢复历史版本失败，请稍后重试。") } finally { restoringVersion.value = null }
  } })
}

onMounted(() => {
  if (getAuthUser()?.role !== "operator") { uni.reLaunch({ url: "/pages/account/index" }); return }
  void loadItems()
})
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="header"><text class="title">运营知识库</text><text class="subtitle">维护内容状态与历史版本</text></view>
    <view class="editor">
      <input v-model="title" placeholder="知识标题" maxlength="200" />
      <textarea v-model="content" placeholder="知识内容" maxlength="20000" auto-height />
      <view class="form-footer"><picker :range="statusOptions.map((item) => statusLabels[item])" :value="statusOptions.indexOf(status)" @change="changeStatus"><view class="status-picker">状态：{{ statusLabels[status] }}</view></picker><view class="form-actions"><button size="mini" :disabled="saving || Boolean(versionsLoading) || restoringVersion !== null" @click="clearForm">新建内容</button><button size="mini" class="primary" :loading="saving" :disabled="saving" @click="saveItem">保存</button></view></view>
      <text v-if="error" class="error">{{ error }}</text>
    </view>
    <view class="list-heading"><text>知识条目</text><button size="mini" :loading="loading" :disabled="loading || Boolean(versionsLoading) || restoringVersion !== null" @click="loadItems">刷新</button></view>
    <view v-if="loading" class="state"><LoadingSpinner size="sm" label="正在加载知识条目" /><text>正在加载知识条目…</text></view>
    <text v-else-if="!items.length" class="state">暂无知识条目，可从上方新建内容。</text>
    <view v-for="item in items" :key="item.id" class="item"><view class="item-copy"><text class="item-title">{{ item.title }}</text><text class="item-meta">{{ statusLabels[item.status] }} · 第 {{ item.version }} 版</text></view><button size="mini" :loading="versionsLoading === item.id" :disabled="Boolean(versionsLoading) || restoringVersion !== null" @click="editItem(item)">编辑</button></view>
    <view v-if="selectedItemId" class="versions"><text class="versions-title">历史版本</text><view v-for="version in versions" :key="version.version" class="version"><view><text class="version-title">第 {{ version.version }} 版 · {{ statusLabels[version.status] }}</text><text class="version-copy">{{ version.content }}</text></view><button size="mini" :loading="restoringVersion === version.version" :disabled="restoringVersion !== null || Boolean(versionsLoading)" @click="restoreVersion(version)">恢复</button></view></view>
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; box-sizing: border-box; padding: 28rpx; background: #f4f7fb; }.header,.editor,.item,.versions { background: #fff; border: 1rpx solid #e1eaf4; border-radius: 18rpx; }.header { padding: 26rpx; }.title,.subtitle,.error,.state,.item-title,.item-meta,.versions-title,.version-title,.version-copy { display: block; }.title { color: #1f2937; font-size: 38rpx; font-weight: 700; }.subtitle { margin-top: 10rpx; color: #64748b; font-size: 24rpx; }.editor,.versions { margin-top: 20rpx; padding: 22rpx; }.editor input,.editor textarea { width: 100%; box-sizing: border-box; margin-top: 12rpx; padding: 16rpx; color: #1f2937; background: #f8fafc; border: 1rpx solid #dfe7f1; border-radius: 12rpx; font-size: 25rpx; }.editor textarea { min-height: 180rpx; }.form-footer,.form-actions,.list-heading,.item,.version { display: flex; align-items: center; justify-content: space-between; gap: 12rpx; }.form-footer { margin-top: 16rpx; }.status-picker { padding: 12rpx 16rpx; color: #245b99; background: #edf6ff; border: 1rpx solid #cfe4fb; border-radius: 10rpx; font-size: 23rpx; }.form-actions button,.list-heading button,.item button,.version button { margin: 0; }.primary { color: #fff; background: #1677ff; }.error { margin-top: 12rpx; color: #c2410c; font-size: 23rpx; }.list-heading { margin-top: 24rpx; }.list-heading text,.versions-title { color: #334155; font-size: 29rpx; font-weight: 700; }.state { margin-top: 14rpx; color: #64748b; font-size: 24rpx; }.item { margin-top: 14rpx; padding: 20rpx; }.item-copy { min-width: 0; }.item-title { color: #1f2937; font-size: 26rpx; font-weight: 700; }.item-meta,.version-copy { margin-top: 6rpx; color: #64748b; font-size: 22rpx; }.versions-title { margin-bottom: 10rpx; }.version { padding: 16rpx 0; border-top: 1rpx solid #e7edf5; }.version > view { min-width: 0; }.version-title { color: #334155; font-size: 24rpx; }.version-copy { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
