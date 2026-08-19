<script setup lang="ts">
import { computed, ref } from "vue"

import ResumePreview from "../../components/ResumePreview.vue"
import { requestPdfExport, requestWordExport } from "../../services/export-api"
import { saveDraft } from "../../services/resume-api"
import { useResumeStore } from "../../stores/resume"
import { getClientId } from "../../stores/session"
import { validateResume } from "../../utils/validators"
import { downloadExport } from "../../utils/download-export"
import { notify } from "../../utils/notifications"

const store = useResumeStore()
const resume = computed(() => store.draft.resume)
const exporting = ref<"word" | "pdf" | "">("")
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
  notify.loading(kind === "pdf" ? "Generating PDF" : "Preparing Word download")
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
    notify.success("Export started")
    finish()
  } catch (reason) {
    finish()
    notify.error(reason instanceof Error ? reason.message : "导出失败，请稍后重试")
  }
}
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
    <view v-if="exporting" class="export-skeleton" aria-live="polite">
      <view class="skeleton-heading"></view>
      <view class="skeleton-line"></view>
      <view class="skeleton-line"></view>
      <view class="skeleton-line short"></view>
    </view>
    <view v-else-if="!hasResumeContent" class="empty-state">
      <view class="empty-illustration" aria-hidden="true"><view></view><view></view><view></view></view>
      <text class="empty-title">Start with your resume details</text>
      <text class="empty-copy">Add your target role and experience before exporting.</text>
      <button class="primary empty-action" @click="backToForm">Fill in resume</button>
    </view>
    <ResumePreview v-else :resume="resume" :template-id="store.draft.templateId" />
  </scroll-view>
</template>

<style scoped>
.page { min-height: 100vh; padding: 28rpx; box-sizing: border-box; overflow-x: hidden; background: #f7f8fa; }
.toolbar { display: flex; justify-content: space-between; gap: 24rpx; align-items: center; margin-bottom: 24rpx; }.title { display: block; color: #1f2329; font-size: 40rpx; font-weight: 700; }.subtitle { display: block; margin-top: 8rpx; color: #86909c; font-size: 23rpx; }
.toolbar-actions { display: flex; gap: 12rpx; }.primary { color: #fff; background: #1677ff; }
.export-skeleton { min-height: 720rpx; padding: 48rpx; background: #fff; border: 1rpx solid #e7edf5; border-radius: 20rpx; }.skeleton-heading,.skeleton-line { height: 24rpx; margin-top: 24rpx; border-radius: 8rpx; background: linear-gradient(90deg, #edf2f7 25%, #f8fafc 40%, #edf2f7 65%); background-size: 400% 100%; animation: shimmer 1.2s ease-in-out infinite; }.skeleton-heading { width: 46%; height: 40rpx; margin-top: 0; }.skeleton-line { width: 100%; }.skeleton-line.short { width: 58%; }@keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: 0 0; } }
.empty-state { padding: 70rpx 32rpx; text-align: center; background: #fff; border: 1rpx solid #e7edf5; border-radius: 20rpx; }.empty-illustration { display: flex; flex-direction: column; gap: 9rpx; width: 126rpx; margin: 0 auto 24rpx; padding: 22rpx; background: #eef6ff; border: 1rpx solid #d4e8ff; border-radius: 18rpx; }.empty-illustration view { height: 10rpx; background: #9fc8f7; border-radius: 999rpx; }.empty-illustration view:nth-child(2) { width: 78%; }.empty-illustration view:nth-child(3) { width: 55%; }.empty-title,.empty-copy { display: block; }.empty-title { color: #1f3e61; font-size: 32rpx; font-weight: 700; }.empty-copy { margin-top: 12rpx; color: #728198; font-size: 24rpx; }.empty-action { margin-top: 26rpx; }
</style>
