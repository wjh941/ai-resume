<script setup lang="ts">
import { computed, onMounted, ref } from "vue"

import ResumePreview from "../../components/ResumePreview.vue"
import { requestPdfExport, requestWordExport } from "../../services/export-api"
import { saveDraft } from "../../services/resume-api"
import { getDraft, toResumeDraft } from "../../services/drafts-api"
import {
  compareResumeVersions,
  createResumeVersion,
  listResumeVersions,
  restoreResumeVersion,
  type ResumeVersion,
} from "../../services/resume-version-api"
import { useResumeStore } from "../../stores/resume"
import { getClientId } from "../../stores/session"
import { validateResume } from "../../utils/validators"
import { downloadExport } from "../../utils/download-export"
import { notify } from "../../utils/notifications"

const store = useResumeStore()
const resume = computed(() => store.draft.resume)
const exporting = ref<"word" | "pdf" | "">("")
const versions = ref<ResumeVersion[]>([])
const versionNote = ref("")
const versionDiff = ref<string[]>([])
const versionLoading = ref(false)
const hasResumeContent = computed(() => Boolean(
  resume.value.basic.name.trim()
  || resume.value.job.targetRole.trim()
  || resume.value.education.length
  || resume.value.employment.length
  || resume.value.projects.length,
))

function backToForm() {
  uni.navigateTo({ url: "/pages/resume-form/index" })
}

function openApplicationTracker() {
  const params = new URLSearchParams()
  if (resume.value.job.targetRole) params.set("roleName", resume.value.job.targetRole)
  if (resume.value.basic.city) params.set("city", resume.value.basic.city)
  if (store.draft.id) params.set("draftId", store.draft.id)
  uni.navigateTo({ url: `/pages/applications/index?${params}` })
}

async function save(): Promise<boolean> {
  const errors = validateResume(resume.value)
  if (errors.length) {
    uni.showToast({ title: errors[0].message, icon: "none" })
    return false
  }
  try {
    const saved = await saveDraft(getClientId(), store.draft)
    store.draft.id = saved.id
    store.checkpoint()
    await loadVersions()
    uni.showToast({ title: "草稿已保存", icon: "success" })
    return true
  } catch {
    store.checkpoint()
    uni.showToast({ title: "网络异常，已保留本地草稿", icon: "none" })
  }
  return false
}

async function exportResume(kind: "word" | "pdf") {
  if (!store.draft.id && !(await save())) return
  if (!store.draft.id) return
  exporting.value = kind
  notify.loading(kind === "pdf" ? "正在生成 PDF" : "正在准备 Word 下载")
  const finish = () => {
    notify.clearLoading()
    exporting.value = ""
  }
  try {
    const result = kind === "word"
      ? await requestWordExport(getClientId(), store.draft.id)
      : await requestPdfExport(getClientId(), store.draft.id)
    await downloadExport(
      result.downloadUrl,
      result.filename,
      process.env.UNI_PLATFORM === "mp-weixin" ? "mp-weixin" : "h5",
    )
    notify.success("已开始导出")
    finish()
  } catch (reason) {
    finish()
    notify.error(reason instanceof Error ? reason.message : "导出失败，请稍后重试")
  }
}

async function loadVersions() {
  if (!store.draft.id) {
    versions.value = []
    return
  }
  try {
    versions.value = await listResumeVersions(store.draft.id)
  } catch {
    versions.value = []
  }
}

async function saveVersion() {
  if (!store.draft.id && !(await save())) return
  if (!store.draft.id) return
  versionLoading.value = true
  try {
    await createResumeVersion(store.draft.id, versionNote.value)
    versionNote.value = ""
    versionDiff.value = []
    await loadVersions()
    uni.showToast({ title: "版本快照已保存", icon: "success" })
  } catch (reason) {
    uni.showToast({ title: reason instanceof Error ? reason.message : "版本快照保存失败，请稍后重试", icon: "none" })
  } finally {
    versionLoading.value = false
  }
}

function restoreVersion(version: ResumeVersion) {
  if (!store.draft.id) return
  uni.showModal({
    title: "恢复版本",
    content: "恢复后将覆盖当前草稿内容，请确认已保存需要保留的修改。",
    success: async (result) => {
      if (!result.confirm || !store.draft.id) return
      try {
        await restoreResumeVersion(store.draft.id, version.id)
        store.draft = toResumeDraft(await getDraft(getClientId(), store.draft.id))
        store.checkpoint()
        versionDiff.value = []
        await loadVersions()
        uni.showToast({ title: "已恢复所选版本", icon: "success" })
      } catch (reason) {
        uni.showToast({ title: reason instanceof Error ? reason.message : "版本恢复失败，请稍后重试", icon: "none" })
      }
    },
  })
}

async function compareVersion(version: ResumeVersion) {
  const active = versions.value.find((item) => item.isActive)
  if (!store.draft.id || !active || active.id === version.id) return
  try {
    versionDiff.value = await compareResumeVersions(store.draft.id, active.id, version.id)
  } catch (reason) {
    uni.showToast({ title: reason instanceof Error ? reason.message : "版本比较失败，请稍后重试", icon: "none" })
  }
}

onMounted(loadVersions)
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="toolbar">
      <view>
        <text class="title">简历预览</text>
        <text class="subtitle">当前模板：{{ store.draft.templateId }}</text>
      </view>
      <view class="toolbar-actions">
        <button size="mini" @click="backToForm">返回填写</button>
        <button size="mini" @click="openApplicationTracker">加入投递计划</button>
        <button size="mini" class="primary" @click="save">保存草稿</button>
        <button size="mini" @click="exportResume('word')">导出 Word</button>
        <button size="mini" @click="exportResume('pdf')">导出 PDF</button>
      </view>
    </view>
    <view class="version-panel">
      <view class="version-heading"><text>简历版本</text><text>快照不会新建草稿</text></view>
      <view class="version-create">
        <input v-model="versionNote" placeholder="版本备注，例如：投递前" />
        <button size="mini" class="primary" :loading="versionLoading" @click="saveVersion">保存版本</button>
      </view>
      <view v-if="versions.length" class="version-list">
        <view v-for="version in versions" :key="version.id" class="version-row">
          <view><text class="version-note">{{ version.note || "未命名版本" }}</text><text class="version-time">{{ version.createdAt }}</text></view>
          <view class="version-actions"><text v-if="version.isActive" class="version-active">当前版本</text><button v-else size="mini" class="secondary" @click="compareVersion(version)">比较</button><button v-if="!version.isActive" size="mini" class="secondary" @click="restoreVersion(version)">恢复</button></view>
        </view>
      </view>
      <text v-else class="version-empty">保存草稿后可创建版本快照。</text>
      <text v-if="versionDiff.length" class="version-diff">差异字段：{{ versionDiff.join("、") }}</text>
    </view>
    <view v-if="exporting" class="export-skeleton" aria-live="polite">
      <view class="skeleton-heading"></view>
      <view class="skeleton-line"></view>
      <view class="skeleton-line"></view>
      <view class="skeleton-line short"></view>
    </view>
    <view v-else-if="!hasResumeContent" class="empty-state">
      <view class="empty-illustration" aria-hidden="true"><view></view><view></view><view></view></view>
      <text class="empty-title">先完善简历内容</text>
      <text class="empty-copy">填写目标岗位和经历后，即可预览、保存版本并导出。</text>
      <button class="primary empty-action" @click="backToForm">去填写简历</button>
    </view>
    <ResumePreview v-else :resume="resume" :template-id="store.draft.templateId" />
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 28rpx; box-sizing: border-box; overflow-x: hidden; background: #f7f8fa; }
.toolbar { display: flex; justify-content: space-between; gap: 24rpx; align-items: center; margin-bottom: 24rpx; }.title { display: block; color: #1f2329; font-size: 40rpx; font-weight: 700; }.subtitle { display: block; margin-top: 8rpx; color: #86909c; font-size: 23rpx; }
.toolbar-actions { display: flex; gap: 12rpx; }.primary { color: #fff; background: #1677ff; }
.version-panel { margin-bottom: 24rpx; padding: 20rpx 22rpx; background: #eef8ff; border: 1rpx solid #c7e5ff; border-radius: 16rpx; }.version-heading,.version-row,.version-actions,.version-create { display: flex; align-items: center; justify-content: space-between; gap: 12rpx; }.version-heading text:first-child { color: #245b99; font-size: 28rpx; font-weight: 700; }.version-heading text:last-child,.version-time,.version-empty { color: #59728d; font-size: 22rpx; }.version-create { margin-top: 14rpx; }.version-create input { flex: 1; height: 64rpx; padding: 0 16rpx; color: #1f2329; background: #fff; border: 1rpx solid #d6e8ff; border-radius: 10rpx; font-size: 24rpx; }.version-create button { flex-shrink: 0; margin: 0; }.version-list { margin-top: 14rpx; }.version-row { padding: 12rpx 0; border-top: 1rpx solid #dceaf7; }.version-note,.version-time { display: block; }.version-note { color: #334e68; font-size: 24rpx; }.version-time { margin-top: 4rpx; }.version-actions { justify-content: flex-end; }.version-actions button { margin: 0; font-size: 21rpx; }.version-active { color: #1677ff; font-size: 22rpx; }.version-empty,.version-diff { display: block; margin-top: 14rpx; line-height: 1.5; }.version-diff { color: #5c4b2a; font-size: 22rpx; }
.export-skeleton { min-height: 720rpx; padding: 48rpx; background: #fff; border: 1rpx solid #e7edf5; border-radius: 20rpx; }.skeleton-heading,.skeleton-line { height: 24rpx; margin-top: 24rpx; border-radius: 8rpx; background: linear-gradient(90deg, #edf2f7 25%, #f8fafc 40%, #edf2f7 65%); background-size: 400% 100%; animation: shimmer 1.2s ease-in-out infinite; }.skeleton-heading { width: 46%; height: 40rpx; margin-top: 0; }.skeleton-line { width: 100%; }.skeleton-line.short { width: 58%; }@keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: 0 0; } }
.empty-state { padding: 70rpx 32rpx; text-align: center; background: #fff; border: 1rpx solid #e7edf5; border-radius: 20rpx; }.empty-illustration { display: flex; flex-direction: column; gap: 9rpx; width: 126rpx; margin: 0 auto 24rpx; padding: 22rpx; background: #eef6ff; border: 1rpx solid #d4e8ff; border-radius: 18rpx; }.empty-illustration view { height: 10rpx; background: #9fc8f7; border-radius: 999rpx; }.empty-illustration view:nth-child(2) { width: 78%; }.empty-illustration view:nth-child(3) { width: 55%; }.empty-title,.empty-copy { display: block; }.empty-title { color: #1f3e61; font-size: 32rpx; font-weight: 700; }.empty-copy { margin-top: 12rpx; color: #728198; font-size: 24rpx; }.empty-action { margin-top: 26rpx; }
</style>
